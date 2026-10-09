"""Small-project DynamoDB backend. All booking writers must use this service.
A global optimistic revision serializes mutations to preserve scan-based limits.
Do not manually mutate bookings/reservations in the console during operation.
"""
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import boto3
from boto3.dynamodb.types import TypeSerializer
from botocore.exceptions import ClientError

SG = timezone(timedelta(hours=8))
SER = TypeSerializer()
GUARD = {'resource_id': 'SYSTEM#BOOKING_STATE', 'slot_start': 'META'}


class ApiError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message
        super().__init__(message)

    def body(self):
        return {'code': self.code, 'message': self.message}


def stamp(dt):
    return dt.astimezone(SG).isoformat(timespec='seconds')


def av(item):
    return {k: SER.serialize(v) for k, v in item.items()}


class DynamoDBService:
    def __init__(self, resource=None, clock=None):
        self.db = resource or boto3.resource('dynamodb')
        self.client = boto3.client('dynamodb',
            region_name=self.db.meta.client.meta.region_name,
            endpoint_url=self.db.meta.client.meta.endpoint_url)
        self.clock = clock or (lambda: datetime.now(SG))
        self.rooms = self.db.Table(os.environ['ROOMS_TABLE'])
        self.users = self.db.Table(os.environ['USERS_TABLE'])
        self.bookings = self.db.Table(os.environ['BOOKINGS_TABLE'])
        self.reservations = self.db.Table(os.environ['RESERVATIONS_TABLE'])

    def scan(self, table):
        items, options = [], {'ConsistentRead': True}
        while True:
            result = table.scan(**options)
            items.extend(result.get('Items', []))
            if not result.get('LastEvaluatedKey'):
                return items
            options['ExclusiveStartKey'] = result['LastEvaluatedKey']

    def get(self, table, key):
        return table.get_item(Key=key, ConsistentRead=True).get('Item')

    def actor(self, uid):
        user = self.get(self.users, {'user_id': uid})
        if not user or user.get('is_active') is not True:
            raise ApiError(403, 'account_inactive', 'Your account is not active.')
        return user

    def identity(self, issuer, subject):
        matches = [u for u in self.scan(self.users)
                   if u.get('auth_issuer') == issuer and u.get('auth_sub') == subject]
        if len(matches) != 1:
            raise ApiError(403, 'identity_unmapped', 'Identity is not mapped to one account.')
        return self.actor(matches[0]['user_id'])

    def room(self, rid):
        r = self.get(self.rooms, {'room_id': rid})
        if not r:
            raise ApiError(404, 'room_not_found', 'Room not found.')
        if r.get('is_active') is not True:
            raise ApiError(400, 'room_inactive', 'Room is inactive.')
        return r

    def revision(self):
        row = self.get(self.reservations, GUARD)
        return int(row.get('revision', 0)) if row else None

    def guard(self, revision):
        put = {'TableName': self.reservations.name,
               'Item': av({**GUARD, 'revision': (revision or 0) + 1})}
        if revision is None:
            put['ConditionExpression'] = 'attribute_not_exists(resource_id)'
        else:
            put['ConditionExpression'] = 'revision = :old'
            put['ExpressionAttributeValues'] = av({':old': revision})
        return {'Put': put}

    def commit(self, actions):
        if len(actions) > 100:
            raise ApiError(400, 'group_too_large', 'Group exceeds this deployment transaction limit.')
        try:
            self.client.transact_write_items(TransactItems=actions)
            return True
        except ClientError as exc:
            code = exc.response['Error']['Code']
            if code in ('TransactionCanceledException', 'TransactionConflictException'):
                reasons = exc.response.get('CancellationReasons', [])
                if any(r.get('Code') in ('ValidationError', 'ItemCollectionSizeLimitExceeded')
                       for r in reasons):
                    raise
                return False
            raise

    def booking(self, bid):
        b = self.get(self.bookings, {'booking_id': bid})
        if not b:
            raise ApiError(404, 'booking_not_found', 'Booking not found.')
        return b

    def view(self, b, viewer):
        outcome = b.get('attendance_outcome', 'pending')
        if b['status'] == 'confirmed' and outcome == 'pending' and \
                self.clock() > datetime.fromisoformat(b['start_time']) + timedelta(minutes=15):
            outcome = 'no_show'
        people = []
        for uid in b['participant_ids']:
            u = self.get(self.users, {'user_id': uid})
            people.append({'user_id': uid, 'name': (u or {}).get('name', uid)})
        return {**{k: b[k] for k in ('booking_id', 'room_id', 'organiser_id', 'start_time',
                                    'end_time', 'status', 'created_at')},
                'participants': people,
                'attendance': {'outcome': outcome, 'check_in_time': b.get('check_in_time')},
                'your_role': 'organiser' if b['organiser_id'] == viewer else 'participant'}

    def list_rooms(self):
        return {'rooms': sorted([r for r in self.scan(self.rooms)
                                 if r.get('is_active') is True], key=lambda r: r['room_id'])}

    def list_users(self, uid):
        self.actor(uid)
        return {'users': sorted([{k: u[k] for k in ('user_id', 'name', 'role')}
                                for u in self.scan(self.users) if u.get('is_active') is True],
                               key=lambda u: u['name'])}

    def availability(self, rid, date):
        if not isinstance(rid, str) or not isinstance(date, str):
            raise ApiError(400, 'invalid_input', 'room_id and date are required.')
        self.room(rid)
        try:
            day = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            raise ApiError(400, 'invalid_input', 'Use YYYY-MM-DD.')
        taken = set()
        options = {'KeyConditionExpression': '#r = :r AND begins_with(#s, :day)',
                   'ExpressionAttributeNames': {'#r': 'resource_id', '#s': 'slot_start'},
                   'ExpressionAttributeValues': {':r': 'ROOM#' + rid, ':day': date + 'T'},
                   'ConsistentRead': True}
        while True:
            result = self.reservations.query(**options)
            taken.update(r['slot_start'] for r in result.get('Items', []))
            if not result.get('LastEvaluatedKey'):
                break
            options['ExclusiveStartKey'] = result['LastEvaluatedKey']
        slots = []
        for hour in range(9, 18):
            start = datetime(day.year, day.month, day.day, hour, tzinfo=SG)
            slots.append({'start_time': stamp(start), 'end_time': stamp(start + timedelta(hours=1)),
                          'available': start > self.clock() and stamp(start) not in taken})
        return {'room_id': rid, 'date': date, 'slots': slots}

    def my_bookings(self, uid):
        self.actor(uid)
        rows = [b for b in self.scan(self.bookings) if uid in b['participant_ids']]
        return {'bookings': [self.view(b, uid) for b in sorted(rows, key=lambda b: b['start_time'])]}

    def all_bookings(self, uid):
        u = self.actor(uid)
        if u.get('role') != 'faculty' and u.get('is_admin') is not True:
            raise ApiError(403, 'not_allowed', 'Staff access required.')
        return {'bookings': [self.view(b, uid) for b in
                             sorted(self.scan(self.bookings), key=lambda b: b['start_time'])]}

    def room_bookings(self, uid, rid, date):
        self.actor(uid)
        self.availability(rid, date)
        rows = [b for b in self.scan(self.bookings)
                if b['room_id'] == rid and b['start_time'].startswith(date + 'T')]
        keys = ('booking_id', 'room_id', 'start_time', 'end_time', 'status')
        return {'room_id': rid, 'date': date,
                'bookings': [{k: b[k] for k in keys} for b in sorted(rows, key=lambda b: b['start_time'])]}

    def create_booking(self, uid, body):
        if not isinstance(body, dict):
            raise ApiError(400, 'invalid_input', 'JSON object required.')
        rid, raw, extras = body.get('room_id'), body.get('start_time'), body.get('participant_ids', [])
        if not isinstance(rid, str) or not rid or not isinstance(raw, str):
            raise ApiError(400, 'invalid_input', 'room_id and start_time are required.')
        if not isinstance(extras, list) or not all(isinstance(x, str) and x for x in extras):
            raise ApiError(400, 'invalid_input', 'participant_ids must contain user IDs.')
        if len(extras) != len(set(extras)):
            raise ApiError(400, 'duplicate_participants', 'Duplicate participants.')
        participants = [uid] + sorted(set(extras) - {uid})
        # Booking + guard + room + user checks + room/user reservations <=100.
        if len(participants) > 47:
            raise ApiError(400, 'group_too_large', 'Maximum group size for this deployment is 47.')
        try:
            start = datetime.fromisoformat(raw.replace('Z', '+00:00'))
            if start.tzinfo is None:
                raise ValueError
            start = start.astimezone(SG)
        except ValueError:
            raise ApiError(400, 'invalid_input', 'start_time must include a timezone.')
        if start.minute or start.second or start.microsecond or not 9 <= start.hour < 18:
            raise ApiError(400, 'invalid_slot', 'Use a whole-hour Singapore slot from 09:00 to 17:00.')
        fingerprint = hashlib.sha256(('|'.join([uid, rid, stamp(start), *sorted(participants)])).encode()).hexdigest()
        for _ in range(5):
            now = self.clock()
            if start <= now:
                raise ApiError(400, 'slot_in_past', 'Choose a future slot.')
            rev = self.revision()  # Read BEFORE scans; conditional guard detects concurrent writers.
            for person in participants:
                self.actor(person)
            room = self.room(rid)
            if len(participants) > int(room['capacity']):
                raise ApiError(400, 'capacity_exceeded', 'Group exceeds room capacity.')
            records = self.scan(self.bookings)
            prior = next((b for b in records if b.get('fingerprint') == fingerprint
                          and b['status'] == 'confirmed'), None)
            if prior:
                return self.view(prior, uid)
            if sum(b['organiser_id'] == uid and b['status'] == 'confirmed'
                   and datetime.fromisoformat(b['start_time']) > now for b in records) >= 2:
                raise ApiError(409, 'booking_limit', 'Maximum two upcoming organised bookings.')
            bid = 'B' + secrets.token_hex(12).upper()
            b = {'booking_id': bid, 'organiser_id': uid, 'room_id': rid,
                 'participant_ids': participants, 'start_time': stamp(start),
                 'end_time': stamp(start + timedelta(hours=1)), 'status': 'confirmed',
                 'created_at': stamp(now), 'fingerprint': fingerprint, 'attendance_outcome': 'pending'}
            actions = [self.guard(rev), {'Put': {'TableName': self.bookings.name,
                       'Item': av(b), 'ConditionExpression': 'attribute_not_exists(booking_id)'}},
                       {'ConditionCheck': {'TableName': self.rooms.name, 'Key': av({'room_id': rid}),
                        'ConditionExpression': 'is_active = :yes AND #cap >= :size',
                        'ExpressionAttributeNames': {'#cap': 'capacity'},
                        'ExpressionAttributeValues': av({':yes': True, ':size': len(participants)})}}]
            for person in participants:
                actions.append({'ConditionCheck': {'TableName': self.users.name,
                    'Key': av({'user_id': person}), 'ConditionExpression': 'is_active = :yes',
                    'ExpressionAttributeValues': av({':yes': True})}})
            for resource in ['ROOM#' + rid] + ['USER#' + p for p in participants]:
                actions.append({'Put': {'TableName': self.reservations.name,
                    'Item': av({'resource_id': resource, 'slot_start': stamp(start), 'booking_id': bid}),
                    'ConditionExpression': 'attribute_not_exists(resource_id)'}})
            if self.commit(actions):
                return self.view(b, uid)
        raise ApiError(409, 'booking_conflict', 'Slot/participant conflict or concurrent change. Refresh and retry.')

    def cancel_booking(self, uid, bid):
        for _ in range(5):
            rev = self.revision()
            actor, b = self.actor(uid), self.booking(bid)
            if b['organiser_id'] != uid and actor.get('is_admin') is not True:
                raise ApiError(403, 'not_allowed', 'Only the organiser or administrator can cancel.')
            if b['status'] != 'confirmed':
                raise ApiError(409, 'already_cancelled', 'Already cancelled.')
            if datetime.fromisoformat(b['start_time']) <= self.clock():
                raise ApiError(409, 'already_started', 'Booking has started.')
            actions = [self.guard(rev), {'Update': {'TableName': self.bookings.name,
                'Key': av({'booking_id': bid}),
                'UpdateExpression': 'SET #st = :cancel, cancelled_at = :now, attendance_outcome = :na',
                'ConditionExpression': '#st = :confirmed',
                'ExpressionAttributeNames': {'#st': 'status'},
                'ExpressionAttributeValues': av({':cancel': 'cancelled', ':confirmed': 'confirmed',
                                                 ':now': stamp(self.clock()), ':na': 'not_applicable'})}}]
            for resource in ['ROOM#' + b['room_id']] + ['USER#' + p for p in b['participant_ids']]:
                actions.append({'Delete': {'TableName': self.reservations.name,
                    'Key': av({'resource_id': resource, 'slot_start': b['start_time']}),
                    'ConditionExpression': 'booking_id = :bid', 'ExpressionAttributeValues': av({':bid': bid})}})
            if self.commit(actions):
                return self.view(self.booking(bid), uid)
        raise ApiError(409, 'concurrent_change', 'Concurrent change. Refresh and retry.')

    def check_in(self, uid, bid):
        for _ in range(5):
            rev = self.revision()
            self.actor(uid)
            b = self.booking(bid)
            if uid not in b['participant_ids']:
                raise ApiError(403, 'not_allowed', 'You are not a participant.')
            if b['status'] != 'confirmed':
                raise ApiError(409, 'booking_cancelled', 'Booking is cancelled.')
            if b.get('attendance_outcome') == 'attended':
                raise ApiError(409, 'already_checked_in', 'Already checked in.')
            now, start = self.clock(), datetime.fromisoformat(b['start_time'])
            if not start <= now <= start + timedelta(minutes=15):
                raise ApiError(409, 'check_in_closed', 'Check-in is available in the first 15 minutes.')
            actions = [self.guard(rev), {'Update': {'TableName': self.bookings.name,
                'Key': av({'booking_id': bid}), 'UpdateExpression': 'SET attendance_outcome = :att, check_in_time = :now',
                'ConditionExpression': '#st = :confirmed AND attendance_outcome = :pending',
                'ExpressionAttributeNames': {'#st': 'status'},
                'ExpressionAttributeValues': av({':att': 'attended', ':now': stamp(now),
                                                 ':confirmed': 'confirmed', ':pending': 'pending'})}}]
            if self.commit(actions):
                return self.view(self.booking(bid), uid)
        raise ApiError(409, 'concurrent_change', 'Concurrent change. Refresh and retry.')

    def admin_rooms(self, uid):
        if self.actor(uid).get('is_admin') is not True:
            raise ApiError(403, 'not_allowed', 'Administrator access required.')
        return {'rooms': sorted(self.scan(self.rooms), key=lambda r: r['room_id'])}

    def save_room(self, uid, body, update=False):
        import re
        if not isinstance(body, dict):
            raise ApiError(400, 'invalid_input', 'JSON object required.')
        rid, cap, active = body.get('room_id'), body.get('capacity'), body.get('is_active')
        if not isinstance(rid, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', rid):
            raise ApiError(400, 'invalid_input', 'Invalid room ID.')
        if type(cap) is not int or not 1 <= cap <= 1000 or type(active) is not bool:
            raise ApiError(400, 'invalid_input', 'Capacity must be an integer 1–1000; is_active must be Boolean.')
        for key in ('name', 'location'):
            if not isinstance(body.get(key), str) or not body[key].strip() or len(body[key]) > 300:
                raise ApiError(400, 'invalid_input', 'Room name and location are required, maximum 300 characters.')
        amenities = body.get('amenities', '')
        if not isinstance(amenities, str) or len(amenities) > 300:
            raise ApiError(400, 'invalid_input', 'Invalid amenities.')
        for _ in range(5):
            rev = self.revision()
            if self.actor(uid).get('is_admin') is not True:
                raise ApiError(403, 'not_allowed', 'Administrator access required.')
            old = self.get(self.rooms, {'room_id': rid})
            if bool(old) != bool(update):
                raise ApiError(409 if old else 404, 'room_exists' if old else 'room_not_found',
                               'Room already exists.' if old else 'Room not found.')
            if any(b['room_id'] == rid and b['status'] == 'confirmed'
                   and datetime.fromisoformat(b['start_time']) > self.clock()
                   and len(b['participant_ids']) > cap for b in self.scan(self.bookings)):
                raise ApiError(409, 'capacity_in_use', 'Capacity is below an existing future booking group.')
            item = {'room_id': rid, 'name': body['name'].strip(), 'location': body['location'].strip(),
                    'capacity': cap, 'is_active': active, 'amenities': amenities}
            actions = [self.guard(rev), {'Put': {'TableName': self.rooms.name, 'Item': av(item),
                'ConditionExpression': 'attribute_exists(room_id)' if update else 'attribute_not_exists(room_id)'}}]
            if self.commit(actions):
                return {'room': item}
        raise ApiError(409, 'concurrent_change', 'Concurrent change. Refresh and retry.')
