"""Roomly booking logic.

This module has no HTTP code in it on purpose. server.py (local) and, later,
the AWS Lambda handler both call the same functions through api.dispatch().

Rules enforced here (see src/booking_rules.md):
- one-hour slots, 09:00-18:00 Asia/Singapore, future only
- active room, one confirmed booking per room per slot
- organiser is always a participant; no duplicate / unknown / inactive participants
- participant count (including organiser) <= room capacity
- a user can be in only one confirmed booking per slot
- an organiser can hold at most 2 future confirmed bookings
- only the organiser (or an admin) can cancel, and only before the start time
- check-in from slot start until 15 minutes after; no-show only after that window

Room + participant reservations are saved in ONE transaction. If anything fails,
nothing is saved. Unique partial indexes are a second line of defence.

The SQLite layer is the local stand-in for DynamoDB. When moving to AWS, the
same checks map to a TransactWriteItems call with condition expressions on
(room_id, slot) and (user_id, slot) lock items.
"""
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

SG = timezone(timedelta(hours=8))
OPEN_HOUR = 9
CLOSE_HOUR = 18
CHECK_IN_GRACE = timedelta(minutes=15)
MAX_FUTURE_BOOKINGS = 2


class ApiError(Exception):
    """A rejected request. status follows the API spec (400/401/403/404/409)."""

    def __init__(self, status, code, message, **extra):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.extra = extra

    def to_body(self):
        return {"code": self.code, "message": self.message, **self.extra}


SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  user_id   TEXT PRIMARY KEY,
  school_id TEXT NOT NULL UNIQUE,
  name      TEXT NOT NULL,
  role      TEXT NOT NULL CHECK(role IN ('student','faculty')),
  is_active INTEGER NOT NULL DEFAULT 1,
  is_admin  INTEGER NOT NULL DEFAULT 0,
  auth_sub  TEXT UNIQUE            -- Cognito 'sub' claim, filled in when auth is connected
);
CREATE TABLE IF NOT EXISTS rooms(
  room_id   TEXT PRIMARY KEY,
  name      TEXT NOT NULL,
  location  TEXT NOT NULL,
  capacity  INTEGER NOT NULL CHECK(capacity > 0),
  is_active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS bookings(
  booking_id   TEXT PRIMARY KEY,
  organiser_id TEXT NOT NULL REFERENCES users(user_id),
  room_id      TEXT NOT NULL REFERENCES rooms(room_id),
  start_time   TEXT NOT NULL,
  end_time     TEXT NOT NULL,
  status       TEXT NOT NULL CHECK(status IN ('confirmed','cancelled')),
  created_at   TEXT NOT NULL,
  cancelled_at TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS one_confirmed_booking_per_room_slot
  ON bookings(room_id, start_time) WHERE status = 'confirmed';
CREATE TABLE IF NOT EXISTS booking_participants(
  booking_id TEXT NOT NULL REFERENCES bookings(booking_id),
  user_id    TEXT NOT NULL REFERENCES users(user_id),
  slot_start TEXT NOT NULL,
  joined_at  TEXT NOT NULL,
  is_active  INTEGER NOT NULL DEFAULT 1,   -- 0 once the booking is cancelled
  PRIMARY KEY(booking_id, user_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_reservation_per_user_slot
  ON booking_participants(user_id, slot_start) WHERE is_active = 1;
CREATE TABLE IF NOT EXISTS attendance(
  booking_id    TEXT PRIMARY KEY REFERENCES bookings(booking_id),
  check_in_time TEXT,
  outcome       TEXT NOT NULL CHECK(outcome IN ('pending','attended','no_show','not_applicable'))
);
"""


SEED_USERS = [
    ("U001", "S-0001", "Alex Tan", "student", 1, 0),
    ("U002", "S-0002", "Jamie Lim", "student", 1, 0),
    ("U003", "S-0003", "Sarah Chen", "student", 1, 0),
    ("U004", "F-0001", "Morgan Lee", "faculty", 1, 0),
    ("U005", "F-0002", "Casey Ng", "faculty", 1, 1),
    ("U006", "S-0006", "Riley Ong", "student", 0, 0),
]
SEED_ROOMS = [
    ("R001", "Study Room A", "Level 2 - Quiet wing", 4, 1),
    ("R002", "Study Room B", "Level 2 - Learning commons", 6, 1),
    ("R003", "Study Room C", "Level 3 - Collaboration zone", 8, 1),
    ("R004", "Study Room D", "Level 3 - Quiet wing", 4, 1),
    ("R005", "Study Room E", "Level 4 - Under maintenance", 6, 0),
]


def iso(dt):
    return dt.astimezone(SG).isoformat(timespec="seconds")


def new_booking_id():
    return "B" + secrets.token_hex(4).upper()


class BookingService:
    def __init__(self, db_path, clock=None):
        self.db_path = str(db_path)
        self.clock = clock or (lambda: datetime.now(SG))
        conn = self._connect()
        try:
            conn.executescript(SCHEMA)
            if conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0] == 0:
                conn.executemany("INSERT INTO rooms VALUES(?,?,?,?,?)", SEED_ROOMS)
            if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
                conn.executemany(
                    "INSERT INTO users(user_id,school_id,name,role,is_active,is_admin) VALUES(?,?,?,?,?,?)",
                    SEED_USERS,
                )
        finally:
            conn.close()

    def now(self):
        return self.clock()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=15, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def _read(self):
        conn = self._connect()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def _write(self):
        """One transaction. BEGIN IMMEDIATE takes the write lock up front, so two
        simultaneous bookings are checked one after the other, never together."""
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.execute("COMMIT")
        except BaseException:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def get_user(self, user_id):
        with self._read() as c:
            row = c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    def get_user_by_sub(self, sub):
        """For Cognito: map the verified token's 'sub' to our Users.user_id."""
        with self._read() as c:
            row = c.execute("SELECT * FROM users WHERE auth_sub=?", (sub,)).fetchone()
        return dict(row) if row else None

    def demo_accounts(self):
        """Local demo login only. Not part of the public API."""
        with self._read() as c:
            rows = c.execute("SELECT user_id,name,role FROM users WHERE is_active=1 ORDER BY user_id")
            return [dict(r) for r in rows]

    def _require_active_user(self, conn, user_id):
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        if not row or not row["is_active"]:
            raise ApiError(403, "account_inactive", "Your account is not active.")
        return row

    def list_rooms(self):
        with self._read() as c:
            rows = c.execute(
                "SELECT room_id,name,location,capacity,is_active FROM rooms WHERE is_active=1 ORDER BY room_id"
            ).fetchall()
        return {"rooms": [{**dict(r), "is_active": bool(r["is_active"])} for r in rows]}

    def list_users(self, user_id):
        """Active users for the participant picker. No school IDs are exposed."""
        with self._read() as c:
            self._require_active_user(c, user_id)
            rows = c.execute(
                "SELECT user_id,name,role FROM users WHERE is_active=1 ORDER BY name"
            ).fetchall()
        return {"users": [dict(r) for r in rows]}

    def availability(self, room_id, date_str):
        if not room_id or not date_str:
            raise ApiError(400, "invalid_input", "room_id and date are required.")
        try:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ApiError(400, "invalid_input", "date must look like 2026-10-01.")
        with self._read() as c:
            room = c.execute("SELECT * FROM rooms WHERE room_id=?", (room_id,)).fetchone()
            if not room:
                raise ApiError(404, "room_not_found", "Room not found.")
            if not room["is_active"]:
                raise ApiError(400, "room_inactive", "This room is not accepting bookings.")
            taken = {
                r["start_time"]
                for r in c.execute(
                    "SELECT start_time FROM bookings WHERE room_id=? AND status='confirmed' AND start_time LIKE ?",
                    (room_id, date_str + "T%"),
                )
            }
        now = self.now()
        slots = []
        for hour in range(OPEN_HOUR, CLOSE_HOUR):
            start = datetime(day.year, day.month, day.day, hour, tzinfo=SG)
            slots.append({
                "start_time": iso(start),
                "end_time": iso(start + timedelta(hours=1)),
                "available": iso(start) not in taken and start > now,
            })
        return {"room_id": room_id, "date": date_str, "slots": slots}

    def my_bookings(self, user_id):
        with self._write() as c:
            self._sweep_no_shows(c)
            rows = c.execute(
                """SELECT * FROM bookings WHERE booking_id IN
                   (SELECT booking_id FROM booking_participants WHERE user_id=?)
                   ORDER BY start_time""",
                (user_id,),
            ).fetchall()
            return {"bookings": [self._view(c, r, viewer=user_id) for r in rows]}

    def all_bookings(self, user_id):
        """Bookings for the faculty/staff overview in the local demo."""
        with self._write() as c:
            actor = self._require_active_user(c, user_id)
            if actor["role"] != "faculty" and not actor["is_admin"]:
                raise ApiError(403, "not_allowed", "Staff access is required.")
            self._sweep_no_shows(c)
            rows = c.execute(
                "SELECT * FROM bookings ORDER BY start_time"
            ).fetchall()
            return {"bookings": [self._view(c, row, viewer=user_id) for row in rows]}

    def create_booking(self, user_id, body):
        if not isinstance(body, dict):
            raise ApiError(400, "invalid_input", "Request body must be a JSON object.")
        room_id = body.get("room_id")
        if not isinstance(room_id, str) or not room_id:
            raise ApiError(400, "invalid_input", "room_id is required.")
        extras = body.get("participant_ids", [])
        if not isinstance(extras, list) or not all(isinstance(x, str) and x for x in extras):
            raise ApiError(400, "invalid_input", "participant_ids must be a list of user IDs.")

        now = self.now()
        start = self._parse_slot_start(body.get("start_time"), now)
        end = start + timedelta(hours=1)

        with self._write() as c:
            organiser = self._require_active_user(c, user_id)

            room = c.execute("SELECT * FROM rooms WHERE room_id=?", (room_id,)).fetchone()
            if not room:
                raise ApiError(404, "room_not_found", "Room not found.")
            if not room["is_active"]:
                raise ApiError(400, "room_inactive", "This room is not accepting bookings.")

            seen, dupes = set(), set()
            for uid in extras:
                if uid in seen:
                    dupes.add(uid)
                seen.add(uid)
            if dupes:
                raise ApiError(400, "duplicate_participants", "Each participant can only be listed once.",
                               user_ids=sorted(dupes))
            others = [u for u in extras if u != organiser["user_id"]]
            everyone = [organiser["user_id"]] + others

            found = {
                r["user_id"]: r
                for r in c.execute(
                    f"SELECT * FROM users WHERE user_id IN ({','.join('?' * len(others))})", others
                )
            } if others else {}
            unknown = [u for u in others if u not in found]
            if unknown:
                raise ApiError(400, "unknown_participants", "Some participants do not exist.", user_ids=unknown)
            inactive = [u for u in others if not found[u]["is_active"]]
            if inactive:
                raise ApiError(400, "inactive_participants", "Some participants have inactive accounts.",
                               user_ids=inactive)

            if len(everyone) > room["capacity"]:
                raise ApiError(400, "capacity_exceeded",
                               f"{room['name']} holds {room['capacity']} people including the organiser.",
                               capacity=room["capacity"], requested=len(everyone))

            future_count = c.execute(
                "SELECT COUNT(*) FROM bookings WHERE organiser_id=? AND status='confirmed' AND start_time>?",
                (organiser["user_id"], iso(now)),
            ).fetchone()[0]
            if future_count >= MAX_FUTURE_BOOKINGS:
                raise ApiError(409, "booking_limit",
                               f"You already have {MAX_FUTURE_BOOKINGS} upcoming bookings. Cancel one first.")

            if c.execute(
                "SELECT 1 FROM bookings WHERE room_id=? AND start_time=? AND status='confirmed'",
                (room_id, iso(start)),
            ).fetchone():
                raise ApiError(409, "slot_taken", "That room is already booked for this slot.")

            busy = [
                r["user_id"]
                for r in c.execute(
                    f"""SELECT user_id FROM booking_participants
                        WHERE is_active=1 AND slot_start=? AND user_id IN ({','.join('?' * len(everyone))})""",
                    [iso(start)] + everyone,
                )
            ]
            if busy:
                raise ApiError(409, "participant_unavailable",
                               "Some participants already have a booking at this time.",
                               user_ids=busy)

            booking_id = new_booking_id()
            stamp = iso(now)
            try:
                c.execute(
                    "INSERT INTO bookings(booking_id,organiser_id,room_id,start_time,end_time,status,created_at)"
                    " VALUES(?,?,?,?,?,'confirmed',?)",
                    (booking_id, organiser["user_id"], room_id, iso(start), iso(end), stamp),
                )
                c.executemany(
                    "INSERT INTO booking_participants(booking_id,user_id,slot_start,joined_at) VALUES(?,?,?,?)",
                    [(booking_id, uid, iso(start), stamp) for uid in everyone],
                )
                c.execute("INSERT INTO attendance(booking_id,outcome) VALUES(?, 'pending')", (booking_id,))
            except sqlite3.IntegrityError:
                raise ApiError(409, "slot_taken", "That slot was just taken. Please choose another.")
            row = c.execute("SELECT * FROM bookings WHERE booking_id=?", (booking_id,)).fetchone()
            return self._view(c, row, viewer=user_id)

    def cancel_booking(self, user_id, booking_id):
        with self._write() as c:
            actor = self._require_active_user(c, user_id)
            booking = self._get_booking(c, booking_id)
            if booking["organiser_id"] != actor["user_id"] and not actor["is_admin"]:
                raise ApiError(403, "not_allowed", "Only the organiser can cancel this booking.")
            if booking["status"] != "confirmed":
                raise ApiError(409, "already_cancelled", "This booking is already cancelled.")
            now = self.now()
            if datetime.fromisoformat(booking["start_time"]) <= now:
                raise ApiError(409, "already_started", "Only bookings that have not started can be cancelled.")
            c.execute("UPDATE bookings SET status='cancelled', cancelled_at=? WHERE booking_id=?",
                      (iso(now), booking_id))
            c.execute("UPDATE booking_participants SET is_active=0 WHERE booking_id=?", (booking_id,))
            c.execute("UPDATE attendance SET outcome='not_applicable' WHERE booking_id=?", (booking_id,))
            row = self._get_booking(c, booking_id)
            return self._view(c, row, viewer=user_id)

    def check_in(self, user_id, booking_id):
        with self._write() as c:
            actor = self._require_active_user(c, user_id)
            self._sweep_no_shows(c)
            booking = self._get_booking(c, booking_id)
            member = c.execute(
                "SELECT 1 FROM booking_participants WHERE booking_id=? AND user_id=?",
                (booking_id, actor["user_id"]),
            ).fetchone()
            if not member:
                raise ApiError(403, "not_allowed", "You are not part of this booking.")
            if booking["status"] != "confirmed":
                raise ApiError(409, "booking_cancelled", "This booking is cancelled.")
            att = c.execute("SELECT * FROM attendance WHERE booking_id=?", (booking_id,)).fetchone()
            if att["outcome"] == "attended":
                raise ApiError(409, "already_checked_in", "Already checked in.")
            now = self.now()
            start = datetime.fromisoformat(booking["start_time"])
            if now < start:
                raise ApiError(409, "check_in_not_open", "Check-in opens at the start time.")
            if now > start + CHECK_IN_GRACE:
                raise ApiError(409, "check_in_closed", "Check-in closed 15 minutes after the start time.")
            c.execute("UPDATE attendance SET check_in_time=?, outcome='attended' WHERE booking_id=?",
                      (iso(now), booking_id))
            row = self._get_booking(c, booking_id)
            return self._view(c, row, viewer=user_id)

    def sweep_no_shows(self):
        """Mark confirmed, still-pending bookings as no_show once the check-in window has closed.
        Runs lazily on reads; on AWS this would be a scheduled (EventBridge) Lambda."""
        with self._write() as c:
            return self._sweep_no_shows(c)

    def _sweep_no_shows(self, c):
        cutoff = iso(self.now() - CHECK_IN_GRACE)
        cur = c.execute(
            """UPDATE attendance SET outcome='no_show'
               WHERE outcome='pending' AND booking_id IN
                 (SELECT booking_id FROM bookings WHERE status='confirmed' AND start_time < ?)""",
            (cutoff,),
        )
        return cur.rowcount

    # ---------- helpers ----------
    def _parse_slot_start(self, value, now):
        if not isinstance(value, str) or not value:
            raise ApiError(400, "invalid_input", "start_time is required.")
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise ApiError(400, "invalid_input", "start_time must look like 2026-10-01T12:00:00+08:00.")
        if dt.tzinfo is None:
            raise ApiError(400, "invalid_input", "start_time must include a timezone.")
        dt = dt.astimezone(SG)
        if dt.minute or dt.second or dt.microsecond:
            raise ApiError(400, "invalid_slot", "Slots start on the hour.")
        if not OPEN_HOUR <= dt.hour < CLOSE_HOUR:
            raise ApiError(400, "invalid_slot", "Slots run from 09:00 to 18:00 Singapore time.")
        if dt <= now:
            raise ApiError(400, "slot_in_past", "Bookings must be for a future time.")
        return dt

    def _get_booking(self, c, booking_id):
        row = c.execute("SELECT * FROM bookings WHERE booking_id=?", (booking_id,)).fetchone()
        if not row:
            raise ApiError(404, "booking_not_found", "Booking not found.")
        return row

    def _view(self, c, row, viewer):
        people = c.execute(
            """SELECT u.user_id, u.name FROM booking_participants p JOIN users u USING(user_id)
               WHERE p.booking_id=? ORDER BY (u.user_id=?) DESC, u.name""",
            (row["booking_id"], row["organiser_id"]),
        ).fetchall()
        att = c.execute("SELECT * FROM attendance WHERE booking_id=?", (row["booking_id"],)).fetchone()
        return {
            "booking_id": row["booking_id"],
            "room_id": row["room_id"],
            "organiser_id": row["organiser_id"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "status": row["status"],
            "created_at": row["created_at"],
            "participants": [dict(p) for p in people],
            "attendance": {"outcome": att["outcome"], "check_in_time": att["check_in_time"]},
            "your_role": "organiser" if row["organiser_id"] == viewer else "participant",
        }