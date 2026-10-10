"""Repeatable tests for the actual DynamoDBService implementation.

These tests use a small in-memory DynamoDB mock rather than the local SQLite
BookingService. This keeps the tests deterministic while exercising the cloud
service's transaction construction, conditions and booking rules.

Run from the repository root:
    python -m unittest tests.test_dynamodb_service -v
"""
import os
import sys
import threading
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dynamodbService import ApiError, DynamoDBService, SG
from fake_dynamodb import FakeDynamoResource

NOW = datetime(2026, 9, 28, 12, 0, tzinfo=SG)
ALEX, JAMIE, SARAH, MORGAN, CASEY = "U001", "U002", "U003", "U004", "U005"


def slot(hour=10, day=1):
    return datetime(2026, 10, day, hour, tzinfo=SG).isoformat(timespec="seconds")


class CloudBase(unittest.TestCase):
    def setUp(self):
        os.environ.update({
            "ROOMS_TABLE": "Rooms",
            "USERS_TABLE": "RoomlyUsers",
            "BOOKINGS_TABLE": "RoomlyBookings",
            "RESERVATIONS_TABLE": "RoomlyReservations",
        })
        self.resource = FakeDynamoResource()
        self.clock = NOW
        self.service = DynamoDBService(self.resource, clock=lambda: self.clock, client=self.resource.client)
        self.seed()

    def seed(self):
        users = [
            (ALEX, "Alex Tan", "student", False),
            (JAMIE, "Jamie Lim", "student", False),
            (SARAH, "Sarah Chen", "student", False),
            (MORGAN, "Morgan Lee", "faculty", False),
            (CASEY, "Casey Ng", "faculty", True),
            ("U006", "Riley Ong", "student", False),
            ("U007", "Extra One", "student", False),
        ]
        for uid, name, role, admin in users:
            self.resource.seed("RoomlyUsers", {
                "user_id": uid, "name": name, "role": role,
                "is_active": True, "is_admin": admin,
                "auth_issuer": "https://issuer.example", "auth_sub": uid,
            })
        for rid, cap in [("R001", 4), ("R002", 6), ("R003", 8), ("R004", 4)]:
            self.resource.seed("Rooms", {
                "room_id": rid, "name": rid, "location": "Campus",
                "capacity": cap, "is_active": True,
            })
        self.resource.seed("Rooms", {
            "room_id": "R005", "name": "Inactive", "location": "Campus",
            "capacity": 6, "is_active": False,
        })

    def book(self, user, room="R001", start=None, participants=None):
        body = {"room_id": room, "start_time": start or slot()}
        if participants is not None:
            body["participant_ids"] = participants
        return self.service.create_booking(user, body)

    def booking_count(self):
        return len(self.resource._tables["RoomlyBookings"])

    def reservation_count(self):
        return len(self.resource._tables["RoomlyReservations"])


class TestDynamoBookingConflicts(CloudBase):
    def race(self, jobs):
        gate = threading.Barrier(len(jobs))
        results = [None] * len(jobs)
        errors = [None] * len(jobs)

        def run(i, job):
            try:
                gate.wait()
                results[i] = job()
            except ApiError as exc:
                results[i] = exc.status
            except Exception as exc:
                errors[i] = exc

        threads = [threading.Thread(target=run, args=(i, job)) for i, job in enumerate(jobs)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        if any(errors):
            raise errors[next(i for i, e in enumerate(errors) if e)]
        return results

    def test_same_room_and_slot_exactly_one_booking_succeeds(self):
        results = self.race([
            lambda: self.book(ALEX, room="R001"),
            lambda: self.book(JAMIE, room="R001"),
        ])
        self.assertEqual(len(results), 2)
        self.assertEqual(self.booking_count(), 1)
        self.assertEqual(sum(isinstance(r, dict) for r in results), 1)
        self.assertEqual(self.reservation_count(), 3)  # guard + room + organiser

    def test_same_participant_different_rooms_exactly_one_booking_succeeds(self):
        results = self.race([
            lambda: self.book(ALEX, room="R001", participants=[SARAH]),
            lambda: self.book(JAMIE, room="R002", participants=[SARAH]),
        ])
        self.assertEqual(self.booking_count(), 1)
        self.assertEqual(sum(isinstance(r, dict) for r in results), 1)
        self.assertEqual(self.reservation_count(), 4)  # guard + room + organiser + shared participant

    def test_repeated_identical_request_returns_existing_booking(self):
        first = self.book(ALEX, room="R002", participants=[JAMIE, SARAH])
        second = self.book(ALEX, room="R002", participants=[SARAH, JAMIE])
        self.assertEqual(first["booking_id"], second["booking_id"])
        self.assertEqual(self.booking_count(), 1)
        self.assertEqual(self.reservation_count(), 5)  # guard + room + organiser + two participants


class TestDynamoRules(CloudBase):
    def test_capacity_and_two_future_booking_limit(self):
        with self.assertRaises(ApiError) as capacity:
            self.book(ALEX, room="R001", participants=[JAMIE, SARAH, MORGAN, "U007"])
        self.assertEqual(getattr(capacity.exception, "code", None), "capacity_exceeded")

        self.book(ALEX, room="R001", start=slot(10))
        self.book(ALEX, room="R002", start=slot(11))
        with self.assertRaises(ApiError) as limit:
            self.book(ALEX, room="R003", start=slot(12))
        self.assertEqual(getattr(limit.exception, "code", None), "booking_limit")

    def test_admin_cannot_be_a_booking_participant(self):
        users = self.service.list_users(ALEX)["users"]
        self.assertNotIn(CASEY, [u["user_id"] for u in users])
        with self.assertRaises(ApiError) as rejected:
            self.book(ALEX, participants=[CASEY])
        self.assertEqual(getattr(rejected.exception, "code", None), "admin_participant_not_allowed")

    def test_admin_cannot_create_booking_when_admin_is_organiser(self):
        with self.assertRaises(ApiError) as rejected:
            self.book(CASEY)
        self.assertEqual(getattr(rejected.exception, "code", None), "admin_participant_not_allowed")


class TestDynamoCancellationAndCheckIn(CloudBase):
    def setUp(self):
        super().setUp()
        self.booking = self.book(ALEX, participants=[JAMIE])
        self.bid = self.booking["booking_id"]

    def test_cancellation_releases_room_and_participant_reservations(self):
        self.assertEqual(self.reservation_count(), 4)  # guard, room, organiser, participant
        cancelled = self.service.cancel_booking(ALEX, self.bid)
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(self.booking_count(), 1)
        self.assertEqual(self.reservation_count(), 1)  # revision guard remains

        replacement = self.book(SARAH, room="R001", participants=[JAMIE])
        self.assertEqual(replacement["status"], "confirmed")

    def test_another_user_cannot_cancel_organisers_booking(self):
        with self.assertRaises(Exception) as rejected:
            self.service.cancel_booking(SARAH, self.bid)
        self.assertEqual(getattr(rejected.exception, "code", None), "not_allowed")
        self.assertEqual(self.service.booking(self.bid)["status"], "confirmed")

    def test_check_in_before_start_is_rejected(self):
        self.clock = datetime.fromisoformat(self.booking["start_time"]) - timedelta(minutes=1)
        with self.assertRaises(Exception) as rejected:
            self.service.check_in(ALEX, self.bid)
        self.assertEqual(getattr(rejected.exception, "code", None), "check_in_closed")

    def test_check_in_inside_window_is_accepted_and_applies_to_booking(self):
        start = datetime.fromisoformat(self.booking["start_time"])
        self.clock = start + timedelta(minutes=5)
        result = self.service.check_in(JAMIE, self.bid)
        self.assertEqual(result["attendance"]["outcome"], "attended")
        self.assertEqual(result["attendance"]["check_in_time"], self.clock.isoformat(timespec="seconds"))

    def test_check_in_after_window_is_rejected_and_view_shows_no_show(self):
        start = datetime.fromisoformat(self.booking["start_time"])
        self.clock = start + timedelta(minutes=16)
        with self.assertRaises(Exception) as rejected:
            self.service.check_in(ALEX, self.bid)
        self.assertEqual(getattr(rejected.exception, "code", None), "check_in_closed")
        self.assertEqual(self.service.my_bookings(ALEX)["bookings"][0]["attendance"]["outcome"], "no_show")


class TestDynamoRoomSequence(CloudBase):
    def test_room_numbers_start_after_highest_existing_room(self):
        result = self.service.save_room(CASEY, {
            "name": "New Room", "location": "Campus", "capacity": 4, "is_active": True,
        })
        self.assertEqual(result["room"]["room_id"], "R006")

    def test_concurrent_room_creation_produces_unique_numbers(self):
        gate = threading.Barrier(4)
        results = []
        errors = []
        lock = threading.Lock()

        def create():
            try:
                gate.wait()
                result = self.service.save_room(CASEY, {
                    "name": "New Room", "location": "Campus", "capacity": 4, "is_active": True,
                })
                with lock:
                    results.append(result["room"]["room_id"])
            except Exception as exc:
                with lock:
                    errors.append(exc)

        threads = [threading.Thread(target=create) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        if errors:
            raise errors[0]
        self.assertEqual(len(results), 4)
        self.assertEqual(len(set(results)), 4)
        self.assertEqual(set(results), {"R006", "R007", "R008", "R009"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
