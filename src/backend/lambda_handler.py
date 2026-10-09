"""HTTP API payload 2.0. Protected routes require an API Gateway JWT authorizer."""
import base64
import json
import logging
import os
import re
from decimal import Decimal

from dynamodbService import ApiError, DynamoDBService, stamp

logger = logging.getLogger()
logger.setLevel(logging.INFO)
_service = None


def service():
    global _service
    if _service is None:
        _service = DynamoDBService()
    return _service


def json_default(value):
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    raise TypeError('Unsupported JSON value')


def response(status, body):
    return {'statusCode': status, 'headers': {'Content-Type': 'application/json', 'Cache-Control': 'no-store'},
            'body': json.dumps(body, default=json_default)}


def lambda_handler(event, context):
    try:
        request = event.get('requestContext', {})
        method = request.get('http', {}).get('method', '')
        path = event.get('rawPath', '').rstrip('/') or '/'
        if path.startswith('/api/'):
            path = path[4:]
        # Claims are provided only after API Gateway verifies the JWT.
        claims = request.get('authorizer', {}).get('jwt', {}).get('claims', {})
        issuer, subject = claims.get('iss'), claims.get('sub')
        if not issuer or not subject:
            raise ApiError(401, 'not_signed_in', 'Verified authentication required.')
        expected = os.environ.get('AUTH_ISSUER')
        if not expected:
            raise ApiError(503, 'auth_not_configured', 'Authentication issuer is not configured.')
        if issuer != expected:
            raise ApiError(401, 'wrong_issuer', 'Invalid authentication issuer.')
        db = service()
        actor = db.identity(issuer, subject)
        uid = actor['user_id']
        raw = event.get('body') or '{}'
        if event.get('isBase64Encoded'):
            raw = base64.b64decode(raw, validate=True).decode('utf-8')
        if len(raw.encode('utf-8')) > 10000:
            raise ApiError(400, 'invalid_input', 'Request body too large.')
        try:
            body = json.loads(raw)
        except (ValueError, TypeError):
            raise ApiError(400, 'invalid_input', 'Invalid JSON.')
        if not isinstance(body, dict):
            raise ApiError(400, 'invalid_input', 'JSON object required.')
        q = event.get('queryStringParameters') or {}
        if method == 'GET' and path == '/admin/rooms':
            return response(200, db.admin_rooms(uid))
        if method == 'POST' and path in ('/admin/rooms/create', '/admin/rooms/update'):
            return response(200 if path.endswith('/update') else 201,
                            db.save_room(uid, body, update=path.endswith('/update')))
        if method == 'GET' and path == '/session':
            return response(200, {'user': {k: actor.get(k) for k in ('user_id', 'name', 'role', 'is_admin')},
                                  'today': db.clock().date().isoformat()})
        if method == 'GET' and path == '/rooms':
            return response(200, db.list_rooms())
        if method == 'GET' and path == '/users':
            return response(200, db.list_users(uid))
        if method == 'GET' and path == '/availability':
            return response(200, db.availability(q.get('room_id'), q.get('date')))
        if method == 'GET' and path == '/my-bookings':
            return response(200, db.my_bookings(uid))
        if method == 'GET' and path == '/all-bookings':
            return response(200, db.all_bookings(uid))
        if method == 'GET' and path == '/room-bookings':
            return response(200, db.room_bookings(uid, q.get('room_id'), q.get('date')))
        if method == 'POST' and path == '/bookings':
            return response(201, db.create_booking(uid, body))
        match = re.fullmatch(r'/bookings/([A-Za-z0-9_-]{1,64})(/check-in)?', path)
        if match and method == 'DELETE' and not match.group(2):
            return response(200, db.cancel_booking(uid, match.group(1)))
        if match and method == 'POST' and match.group(2):
            return response(200, db.check_in(uid, match.group(1)))
        raise ApiError(404, 'route_not_found', 'Route is not implemented by this backend.')
    except ApiError as exc:
        return response(exc.status, exc.body())
    except (UnicodeError, ValueError) as exc:
        return response(400, {'code': 'invalid_input', 'message': 'Invalid encoded request.'})
    except Exception:
        logger.exception('Cloud backend failure request_id=%s', getattr(context, 'aws_request_id', 'unknown'))
        return response(500, {'code': 'internal_error', 'message': 'Service temporarily unavailable.'})
