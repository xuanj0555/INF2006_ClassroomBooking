"""Admin room management and historical analytics, sharing the booking schema.
Historical reservations are never inserted into live bookings or rooms.
"""
import csv
from datetime import date
from pathlib import Path
from bookingService import ApiError, BookingService, iso


class RoomlyService(BookingService):
    def __init__(self, db_path, clock=None, history_csv=None):
        super().__init__(db_path, clock)
        with self._write() as c:
            columns = {r['name'] for r in c.execute('PRAGMA table_info(rooms)')}
            if 'amenities' not in columns:
                c.execute("ALTER TABLE rooms ADD COLUMN amenities TEXT NOT NULL DEFAULT ''")
            c.execute('''CREATE TABLE IF NOT EXISTS reservations_history(
                start_time TEXT, end_time TEXT, duration_minutes REAL, room_id TEXT,
                reservation_date TEXT, weekday TEXT, start_hour INTEGER,
                month INTEGER, is_weekend INTEGER)''')
            if history_csv and Path(history_csv).exists() and not c.execute(
                'SELECT 1 FROM reservations_history LIMIT 1').fetchone():
                with open(history_csv, newline='', encoding='utf-8-sig') as f:
                    first = f.readline()
                    if first.startswith('start_time,'):
                        f.seek(0)
                    rows = []
                    for r in csv.DictReader(f):
                        day = r.get('reservation_date') or r.get('booking_date')
                        date.fromisoformat(day)
                        rows.append((r['start_time'], r['end_time'], float(r['duration_minutes']),
                                     r['room_id'], day, r['weekday'], int(r['start_hour']),
                                     int(r['month']), int(r['is_weekend'].strip().lower() in ('true','1'))))
                    c.executemany('INSERT INTO reservations_history VALUES(?,?,?,?,?,?,?,?,?)', rows)

    def _admin(self, c, user_id):
        actor = self._require_active_user(c, user_id)
        if not actor['is_admin']:
            raise ApiError(403, 'admin_required', 'Administrator access required.')

    def admin_rooms(self, user_id):
        with self._read() as c:
            self._admin(c, user_id)
            return {'rooms': [dict(r) for r in c.execute('SELECT * FROM rooms ORDER BY room_id')]}

    def save_room(self, user_id, body, update=False):
        with self._write() as c:
            self._admin(c, user_id)
            if not isinstance(body, dict):
                raise ApiError(400, 'invalid_input', 'A JSON object is required.')
            fields = {}
            for key in ('name', 'location', 'amenities'):
                value = body.get(key, '')
                if not isinstance(value, str) or len(value) > 300:
                    raise ApiError(400, 'invalid_input', f'{key} must be text of at most 300 characters.')
                fields[key] = value.strip()
            cap = body.get('capacity')
            if isinstance(cap, bool) or not isinstance(cap, int) or not 1 <= cap <= 1000:
                raise ApiError(400, 'invalid_input', 'Capacity must be a whole number from 1 to 1000.')
            active = body.get('is_active', True)
            if not isinstance(active, bool) or not fields['name'] or not fields['location']:
                raise ApiError(400, 'invalid_input', 'Name, location and a boolean is_active are required.')
            if update:
                rid = body.get('room_id')
                if not isinstance(rid, str) or not c.execute('SELECT 1 FROM rooms WHERE room_id=?', (rid,)).fetchone():
                    raise ApiError(404, 'room_not_found', 'Room not found.')
                largest = c.execute('''SELECT COUNT(*) AS n FROM booking_participants p
                    JOIN bookings b USING(booking_id)
                    WHERE b.room_id=? AND b.status='confirmed' AND b.end_time>?
                    GROUP BY b.booking_id ORDER BY n DESC LIMIT 1''', (rid, iso(self.now()))).fetchone()
                if largest and cap < largest['n']:
                    raise ApiError(409, 'existing_booking_capacity', 'Capacity is below an existing upcoming group size.')
                c.execute('UPDATE rooms SET name=?,location=?,capacity=?,is_active=?,amenities=? WHERE room_id=?',
                          (fields['name'], fields['location'], cap, int(active), fields['amenities'], rid))
            else:
                ids = [r[0] for r in c.execute('SELECT room_id FROM rooms')]
                number = max([int(x[1:]) for x in ids if x.startswith('R') and x[1:].isdigit()] or [0]) + 1
                rid = f'R{number:03d}'
                c.execute('INSERT INTO rooms(room_id,name,location,capacity,is_active,amenities) VALUES(?,?,?,?,?,?)',
                          (rid, fields['name'], fields['location'], cap, int(active), fields['amenities']))
            return {'room_id': rid, 'message': 'Room updated.' if update else 'Room added.'}

    def reservation_analytics(self, user_id):
        with self._read() as c:
            self._admin(c, user_id)
            total = c.execute('SELECT COUNT(*) FROM reservations_history').fetchone()[0]
            result = {'source': 'Historical reservations CSV (separate from live bookings)', 'total': total}
            if not total:
                return result
            start, end = c.execute('SELECT MIN(reservation_date),MAX(reservation_date) FROM reservations_history').fetchone()
            order = "CASE weekday WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3 WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6 ELSE 7 END"
            result.update(date_from=start, date_to=end,
                by_room=[dict(r) for r in c.execute('SELECT room_id,COUNT(*) count FROM reservations_history GROUP BY room_id ORDER BY count DESC,room_id LIMIT 12')],
                by_weekday=[dict(r) for r in c.execute(f'SELECT weekday,COUNT(*) count FROM reservations_history GROUP BY weekday ORDER BY {order}')],
                by_hour=[dict(r) for r in c.execute('SELECT start_hour hour,COUNT(*) count FROM reservations_history GROUP BY start_hour ORDER BY hour')],
                by_month=[dict(r) for r in c.execute('SELECT month,COUNT(*) count FROM reservations_history GROUP BY month ORDER BY month')])
            avg, weekend, duration = c.execute('SELECT AVG(duration_minutes),SUM(is_weekend),SUM(duration_minutes) FROM reservations_history').fetchone()
            result.update(avg_duration_minutes=round(avg,1),weekend_share=round(weekend/total,3),reserved_hours=round(duration/60,2))
            return result

    def demand_patterns(self, user_id):
        with self._read() as c:
            self._admin(c, user_id)
            total = c.execute('SELECT COUNT(*) FROM reservations_history').fetchone()[0]
            return {
                'method': 'Historical reservation counts only; no trained or validated forecast',
                'total_samples': total,
                'busiest_slots': [dict(r) for r in c.execute('SELECT weekday,start_hour hour,COUNT(*) count FROM reservations_history GROUP BY weekday,start_hour ORDER BY count DESC,weekday,start_hour LIMIT 10')],
                'likely_busiest_rooms': [dict(r) for r in c.execute('SELECT room_id,COUNT(*) count FROM reservations_history GROUP BY room_id ORDER BY count DESC,room_id LIMIT 8')],
            }
