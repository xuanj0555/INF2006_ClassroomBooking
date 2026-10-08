"""Backend tests. Run from the repo root:  python -m unittest tests.test_backend -v
(or)                                       python tests/test_backend.py

Uses a controlled clock, so the tests keep working after the fixed sample dates
in data/ become past dates. Sample users/rooms: see SEED_USERS / SEED_ROOMS.
"""
import os
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "backend"))
from API import dispatch
from bookingService import SG, BookingService

NOW = datetime(2026, 9, 28, 12, 0, tzinfo=SG)
ALEX, JAMIE, SARAH, MORGAN, CASEY, RILEY = "U001", "U002", "U003", "U004", "U005", "U006"


def slot(day=1, hour=10, month=10):
    """Slot start string, e.g. 2026-10-01T10:00:00+08:00 (always in the future of NOW)."""
    return datetime(2026, month, day, hour, tzinfo=SG).isoformat(timespec="seconds")


class Base(unittest.TestCase):
    def setUp(self):
        fd, self.db = tempfile.mkstemp(suffix=".sqlite3")
        os.close(fd)
        os.unlink(self.db)
        self.clock = NOW
        self.svc = BookingService(self.db, clock=lambda: self.clock)

    def tearDown(self):
        for suffix in ("", "-wal", "-shm", "-journal"):
            try:
                os.unlink(self.db + suffix)
            except FileNotFoundError:
                pass

    def call(self, user, method, path, body=None, query=None):
        return dispatch(self.svc, method, path, query, body, user)

    def book(self, user, room="R001", start=None, participants=None):
        body = {"room_id": room, "start_time": start or slot()}
        if participants is not None:
            body["participant_ids"] = participants
        return self.call(user, "POST", "/bookings", body)

    def count(self, table):
        with self.svc._read() as c:
            return c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


class TestCreate(Base):
    def test_valid_booking_confirmed_and_organiser_included(self):
        status, b = self.book(ALEX, participants=[JAMIE])
        self.assertEqual(status, 201)
        self.assertEqual(b["status"], "confirmed")
        self.assertEqual(b["organiser_id"], ALEX)
        self.assertEqual(b["end_time"], slot(hour=11))
        self.assertEqual({p["user_id"] for p in b["participants"]}, {ALEX, JAMIE})
        self.assertEqual(b["attendance"]["outcome"], "pending")

    def test_browser_cannot_choose_owner_or_status(self):
        status, b = self.call(ALEX, "POST", "/bookings", {
            "room_id": "R001", "start_time": slot(), "organiser_id": JAMIE,
            "user_id": JAMIE, "status": "cancelled", "booking_id": "HACK"})
        self.assertEqual(status, 201)
        self.assertEqual(b["organiser_id"], ALEX)
        self.assertEqual(b["status"], "confirmed")
        self.assertNotEqual(b["booking_id"], "HACK")

    def test_not_signed_in_is_401(self):
        status, _ = self.call(None, "POST", "/bookings", {"room_id": "R001", "start_time": slot()})
        self.assertEqual(status, 401)

    def test_inactive_account_is_403(self):
        status, body = self.book(RILEY)
        self.assertEqual((status, body["code"]), (403, "account_inactive"))

    def test_same_room_same_slot_conflict(self):
        self.assertEqual(self.book(ALEX)[0], 201)
        status, body = self.book(JAMIE)
        self.assertEqual((status, body["code"]), (409, "slot_taken"))

    def test_inactive_room_rejected(self):
        status, body = self.book(ALEX, room="R005")
        self.assertEqual((status, body["code"]), (400, "room_inactive"))

    def test_unknown_room_404(self):
        self.assertEqual(self.book(ALEX, room="R999")[0], 404)

    def test_invalid_input_400(self):
        bad = [
            {},                                     
            {"room_id": "R001"},                             
            {"room_id": "R001", "start_time": "2026-10-01"}, 
            {"room_id": "R001", "start_time": "2026-10-01T10:00:00"}, 
            {"room_id": "R001", "start_time": "not a date"},
            {"room_id": "R001", "start_time": slot(), "participant_ids": "U002"},
            {"room_id": "R001", "start_time": slot(), "participant_ids": [5]},
            {"start_time": slot()},
        ]
        for body in bad:
            with self.subTest(body=body):
                self.assertEqual(self.call(ALEX, "POST", "/bookings", body)[0], 400)

    def test_slot_rules(self):
        cases = {
            "half hour": datetime(2026, 10, 1, 10, 30, tzinfo=SG),
            "before opening": datetime(2026, 10, 1, 8, 0, tzinfo=SG),
            "at closing time": datetime(2026, 10, 1, 18, 0, tzinfo=SG),
            "past": datetime(2026, 9, 27, 10, 0, tzinfo=SG),
            "earlier today": datetime(2026, 9, 28, 10, 0, tzinfo=SG),
        }
        for name, dt in cases.items():
            with self.subTest(name):
                self.assertEqual(self.book(ALEX, start=dt.isoformat())[0], 400)
        self.assertEqual(self.book(ALEX, start=slot(hour=17))[0], 201)

    def test_other_timezone_is_converted_to_singapore(self):
        status, b = self.book(ALEX, start="2026-10-01T02:00:00+00:00")
        self.assertEqual(status, 201)
        self.assertEqual(b["start_time"], slot(hour=10))

    def test_organiser_id_in_participants_is_harmless(self):
        status, b = self.book(ALEX, participants=[ALEX, JAMIE])
        self.assertEqual(status, 201)
        self.assertEqual(len(b["participants"]), 2)

    def test_duplicate_unknown_inactive_participants_rejected(self):
        s, body = self.book(ALEX, participants=[JAMIE, JAMIE])
        self.assertEqual((s, body["code"]), (400, "duplicate_participants"))
        s, body = self.book(ALEX, participants=["U999"])
        self.assertEqual((s, body["code"]), (400, "unknown_participants"))
        s, body = self.book(ALEX, participants=[RILEY])
        self.assertEqual((s, body["code"]), (400, "inactive_participants"))
        self.assertEqual(self.count("bookings"), 0)

    def test_capacity_enforced_including_organiser(self):
        self.assertEqual(self.book(ALEX, participants=[JAMIE, SARAH, MORGAN])[0], 201)
        with self.svc._write() as c:
            c.execute("INSERT INTO users VALUES('U007','S-0007','Extra One','student',1,0,NULL)")
        status, body = self.book(CASEY, room="R004", start=slot(hour=12),
                                 participants=[JAMIE, SARAH, MORGAN, "U007"])
        self.assertEqual((status, body["code"]), (400, "capacity_exceeded"))
        self.assertEqual(body["capacity"], 4)

    def test_participant_already_booked_rejected_and_nothing_saved(self):
        self.assertEqual(self.book(ALEX, room="R001", participants=[JAMIE])[0], 201)
        bookings, people = self.count("bookings"), self.count("booking_participants")
        status, body = self.book(SARAH, room="R002", participants=[JAMIE])
        self.assertEqual((status, body["code"]), (409, "participant_unavailable"))
        self.assertEqual(body["user_ids"], [JAMIE])
        self.assertEqual(self.count("bookings"), bookings)
        self.assertEqual(self.count("booking_participants"), people)
        self.assertEqual(self.book(SARAH, room="R002")[0], 201)

    def test_organiser_cannot_be_in_two_rooms_same_slot(self):
        self.assertEqual(self.book(ALEX, room="R001")[0], 201)
        status, body = self.book(ALEX, room="R002")
        self.assertEqual((status, body["code"]), (409, "participant_unavailable"))

    def test_participant_can_be_in_different_slots(self):
        self.assertEqual(self.book(ALEX, participants=[JAMIE], start=slot(hour=10))[0], 201)
        self.assertEqual(self.book(SARAH, participants=[JAMIE], start=slot(hour=11))[0], 201)

    def test_organiser_limit_two_future_bookings(self):
        self.assertEqual(self.book(ALEX, start=slot(hour=10))[0], 201)
        self.assertEqual(self.book(ALEX, start=slot(hour=11))[0], 201)
        status, body = self.book(ALEX, start=slot(hour=12))
        self.assertEqual((status, body["code"]), (409, "booking_limit"))

    def test_cancelled_bookings_do_not_count_toward_limit(self):
        _, b1 = self.book(ALEX, start=slot(hour=10))
        self.book(ALEX, start=slot(hour=11))
        self.assertEqual(self.call(ALEX, "DELETE", f"/bookings/{b1['booking_id']}")[0], 200)
        self.assertEqual(self.book(ALEX, start=slot(hour=12))[0], 201)

    def test_being_a_participant_does_not_use_up_organiser_limit(self):
        self.book(JAMIE, room="R001", start=slot(hour=10), participants=[ALEX])
        self.book(JAMIE, room="R002", start=slot(hour=11), participants=[ALEX])
        self.assertEqual(self.book(ALEX, start=slot(hour=12))[0], 201)

    def test_repeated_identical_submission_returns_same_booking(self):
        body = {
            "room_id": "R001",
            "start_time": slot(hour=10),
            "participant_ids": [JAMIE, SARAH],
        }
        first_status, first = self.call(ALEX, "POST", "/bookings", body)
        second_status, second = self.call(ALEX, "POST", "/bookings", body)
        self.assertEqual(first_status, 201)
        self.assertEqual(second_status, 201)
        self.assertEqual(second["booking_id"], first["booking_id"])
        self.assertEqual(self.count("bookings"), 1)
        self.assertEqual(self.count("booking_participants"), 3)

    def test_repeated_submission_with_participants_in_different_order_is_same_request(self):
        first_status, first = self.book(ALEX, participants=[JAMIE, SARAH])
        second_status, second = self.book(ALEX, participants=[SARAH, JAMIE])
        self.assertEqual((first_status, second_status), (201, 201))
        self.assertEqual(first["booking_id"], second["booking_id"])
        self.assertEqual(self.count("bookings"), 1)


class TestCancel(Base):
    def setUp(self):
        super().setUp()
        _, self.b = self.book(ALEX, participants=[JAMIE])
        self.path = f"/bookings/{self.b['booking_id']}"

    def test_other_user_cannot_cancel(self):
        status, body = self.call(SARAH, "DELETE", self.path)
        self.assertEqual((status, body["code"]), (403, "not_allowed"))
        self.assertEqual(self.call(ALEX, "GET", "/my-bookings")[1]["bookings"][0]["status"], "confirmed")

    def test_participant_cannot_cancel_whole_booking(self):
        self.assertEqual(self.call(JAMIE, "DELETE", self.path)[0], 403)

    def test_faculty_status_alone_is_not_admin(self):
        self.assertEqual(self.call(MORGAN, "DELETE", self.path)[0], 403)

    def test_organiser_cancel_releases_room_and_participants_but_keeps_record(self):
        status, body = self.call(ALEX, "DELETE", self.path)
        self.assertEqual((status, body["status"]), (200, "cancelled"))
        self.assertEqual(body["attendance"]["outcome"], "not_applicable")
        for who in (ALEX, JAMIE):
            rows = self.call(who, "GET", "/my-bookings")[1]["bookings"]
            self.assertEqual([r["status"] for r in rows], ["cancelled"])
        slots = self.call(ALEX, "GET", "/availability", query={"room_id": "R001", "date": "2026-10-01"})[1]["slots"]
        self.assertTrue(next(s for s in slots if s["start_time"] == slot())["available"])
        self.assertEqual(self.book(SARAH, room="R001", participants=[JAMIE])[0], 201)

    def test_admin_can_cancel_future_booking(self):
        self.assertEqual(self.call(CASEY, "DELETE", self.path)[0], 200)

    def test_cancel_twice_is_409(self):
        self.call(ALEX, "DELETE", self.path)
        status, body = self.call(ALEX, "DELETE", self.path)
        self.assertEqual((status, body["code"]), (409, "already_cancelled"))

    def test_cannot_cancel_after_start(self):
        self.clock = datetime(2026, 10, 1, 10, 5, tzinfo=SG)
        status, body = self.call(ALEX, "DELETE", self.path)
        self.assertEqual((status, body["code"]), (409, "already_started"))

    def test_unknown_booking_404(self):
        self.assertEqual(self.call(ALEX, "DELETE", "/bookings/NOPE")[0], 404)


class TestConcurrency(Base):
    def race(self, jobs):
        """Fire the jobs at the same moment from separate threads, return their statuses."""
        gate, results = threading.Barrier(len(jobs)), [None] * len(jobs)

        def run(i, job):
            gate.wait()
            results[i] = job()[0]

        threads = [threading.Thread(target=run, args=(i, j)) for i, j in enumerate(jobs)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        return results

    def test_two_users_one_room_slot_exactly_one_wins(self):
        for _ in range(5):
            self.setUp()
            res = self.race([lambda: self.book(ALEX, room="R002"), lambda: self.book(JAMIE, room="R002")])
            self.assertEqual(sorted(res), [201, 409])
            self.assertEqual(self.count("bookings"), 1)

    def test_two_rooms_same_participant_exactly_one_wins(self):
        res = self.race([
            lambda: self.book(ALEX, room="R001", participants=[SARAH]),
            lambda: self.book(JAMIE, room="R002", participants=[SARAH]),
        ])
        self.assertEqual(sorted(res), [201, 409])
        self.assertEqual(self.count("bookings"), 1)
        self.assertEqual(self.count("booking_participants"), 2)

    def test_many_users_same_slot_exactly_one_wins(self):
        users = [ALEX, JAMIE, SARAH, MORGAN, CASEY]
        res = self.race([(lambda u=u: self.book(u, room="R003")) for u in users])
        self.assertEqual(res.count(201), 1)
        self.assertEqual(res.count(409), 4)


class TestUniqueIndexBackstop(Base):
    def test_database_itself_refuses_double_reservation(self):
        """Even if the Python checks were bypassed, the DB must reject it."""
        import sqlite3
        self.book(ALEX)
        with self.svc._write() as c:
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute("INSERT INTO bookings VALUES('X1',?, 'R001',?,?, 'confirmed',?,NULL)",
                          (JAMIE, slot(), slot(hour=11), slot()))


class TestCheckInAndNoShow(Base):
    def setUp(self):
        super().setUp()
        _, self.b = self.book(ALEX, participants=[JAMIE])
        self.id = self.b["booking_id"]
        self.start = datetime.fromisoformat(self.b["start_time"])

    def check_in(self, user):
        return self.call(user, "POST", f"/bookings/{self.id}/check-in")

    def outcome(self):
        return self.call(ALEX, "GET", "/my-bookings")[1]["bookings"][0]["attendance"]["outcome"]

    def test_check_in_inside_window(self):
        self.clock = self.start + timedelta(minutes=5)
        status, body = self.check_in(ALEX)
        self.assertEqual((status, body["attendance"]["outcome"]), (200, "attended"))
        self.assertEqual(self.outcome(), "attended")

    def test_check_in_window_edges(self):
        self.clock = self.start                       
        self.assertEqual(self.check_in(ALEX)[0], 200)

    def test_last_minute_of_window_still_ok(self):
        self.clock = self.start + timedelta(minutes=15)
        self.assertEqual(self.check_in(JAMIE)[0], 200)

    def test_too_early_rejected(self):
        self.clock = self.start - timedelta(minutes=1)
        status, body = self.check_in(ALEX)
        self.assertEqual((status, body["code"]), (409, "check_in_not_open"))

    def test_too_late_rejected_and_becomes_no_show(self):
        self.clock = self.start + timedelta(minutes=16)
        status, body = self.check_in(ALEX)
        self.assertEqual((status, body["code"]), (409, "check_in_closed"))
        self.assertEqual(self.outcome(), "no_show")

    def test_not_no_show_while_window_still_open(self):
        self.clock = self.start + timedelta(minutes=10)
        self.assertEqual(self.outcome(), "pending")

    def test_no_show_recorded_only_after_window_closes(self):
        self.clock = self.start + timedelta(minutes=15, seconds=1)
        self.assertEqual(self.svc.sweep_no_shows(), 1)
        self.assertEqual(self.outcome(), "no_show")

    def test_attended_booking_is_never_marked_no_show(self):
        self.clock = self.start + timedelta(minutes=2)
        self.check_in(ALEX)
        self.clock = self.start + timedelta(hours=3)
        self.assertEqual(self.svc.sweep_no_shows(), 0)
        self.assertEqual(self.outcome(), "attended")

    def test_cancelled_booking_is_not_a_no_show(self):
        self.call(ALEX, "DELETE", f"/bookings/{self.id}")
        self.clock = self.start + timedelta(hours=3)
        self.svc.sweep_no_shows()
        self.assertEqual(self.outcome(), "not_applicable")
        self.assertEqual(self.check_in(ALEX)[1]["code"], "booking_cancelled")

    def test_outsider_cannot_check_in(self):
        self.clock = self.start + timedelta(minutes=1)
        self.assertEqual(self.check_in(SARAH)[0], 403)

    def test_double_check_in_rejected(self):
        self.clock = self.start + timedelta(minutes=1)
        self.check_in(ALEX)
        self.assertEqual(self.check_in(ALEX)[1]["code"], "already_checked_in")


class TestReads(Base):
    def test_rooms_only_active_and_shape(self):
        status, body = self.call(ALEX, "GET", "/rooms")
        self.assertEqual(status, 200)
        ids = [r["room_id"] for r in body["rooms"]]
        self.assertEqual(ids, ["R001", "R002", "R003", "R004"])
        self.assertEqual(set(body["rooms"][0]), {"room_id", "name", "location", "capacity", "is_active"})
        self.assertIs(body["rooms"][0]["is_active"], True)

    def test_availability_marks_booked_and_past_slots(self):
        self.book(ALEX, room="R001", start=slot(hour=10))
        status, body = self.call(JAMIE, "GET", "/availability", query={"room_id": "R001", "date": "2026-10-01"})
        self.assertEqual(status, 200)
        self.assertEqual(len(body["slots"]), 9)
        by_start = {s["start_time"]: s["available"] for s in body["slots"]}
        self.assertFalse(by_start[slot(hour=10)])
        self.assertTrue(by_start[slot(hour=11)])
        _, today = self.call(JAMIE, "GET", "/availability", query={"room_id": "R001", "date": "2026-09-28"})
        avail = {s["start_time"][11:16]: s["available"] for s in today["slots"]}
        self.assertFalse(avail["11:00"])
        self.assertTrue(avail["13:00"])

    def test_availability_validation(self):
        self.assertEqual(self.call(ALEX, "GET", "/availability", query={"date": "2026-10-01"})[0], 400)
        self.assertEqual(self.call(ALEX, "GET", "/availability", query={"room_id": "R001", "date": "1 Oct"})[0], 400)
        self.assertEqual(self.call(ALEX, "GET", "/availability", query={"room_id": "R999", "date": "2026-10-01"})[0], 404)
        self.assertEqual(self.call(ALEX, "GET", "/availability", query={"room_id": "R005", "date": "2026-10-01"})[0], 400)

    def test_my_bookings_only_shows_own_and_joined(self):
        self.book(ALEX, room="R001", participants=[JAMIE])
        self.book(SARAH, room="R002")
        alex = self.call(ALEX, "GET", "/my-bookings")[1]["bookings"]
        jamie = self.call(JAMIE, "GET", "/my-bookings")[1]["bookings"]
        self.assertEqual([b["your_role"] for b in alex], ["organiser"])
        self.assertEqual([b["your_role"] for b in jamie], ["participant"])
        self.assertEqual(len(self.call(MORGAN, "GET", "/my-bookings")[1]["bookings"]), 0)

    def test_room_bookings_returns_bookings_for_room_and_date(self):
        self.book(ALEX, room="R001", start=slot(hour=10))
        self.book(SARAH, room="R001", start=slot(hour=11))
        status, body = self.call(
            JAMIE, "GET", "/room-bookings",
            query={"room_id": "R001", "date": "2026-10-01"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["room_id"], "R001")
        self.assertEqual([b["start_time"] for b in body["bookings"]], [slot(hour=10), slot(hour=11)])
        self.assertEqual([b["status"] for b in body["bookings"]], ["confirmed", "confirmed"])

    def test_room_bookings_does_not_return_other_room(self):
        self.book(ALEX, room="R001", start=slot(hour=10))
        self.book(SARAH, room="R002", start=slot(hour=11))
        status, body = self.call(
            JAMIE, "GET", "/room-bookings",
            query={"room_id": "R001", "date": "2026-10-01"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(body["bookings"]), 1)
        self.assertEqual(body["bookings"][0]["room_id"], "R001")

    def test_users_list_hides_inactive_and_school_ids(self):
        status, body = self.call(ALEX, "GET", "/users")
        self.assertEqual(status, 200)
        ids = [u["user_id"] for u in body["users"]]
        self.assertNotIn(RILEY, ids)
        self.assertEqual(set(body["users"][0]), {"user_id", "name", "role"})

    def test_unknown_route_and_method(self):
        self.assertEqual(self.call(ALEX, "GET", "/nope")[0], 404)
        self.assertEqual(self.call(ALEX, "GET", "/bookings")[0], 404)
        self.assertEqual(self.call(None, "GET", "/rooms")[0], 401)


if __name__ == "__main__":
    unittest.main(verbosity=2)