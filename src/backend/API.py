"""Routes requests to BookingService. No HTTP server code, no auth code.

dispatch() takes an already-verified user_id (or None) and returns (status, body).
- server.py calls it after checking the demo session cookie.
- The Lambda handler will call it after API Gateway / Cognito has verified the token
  and the token's 'sub' has been mapped to Users.user_id.
"""
import re

from bookingService import ApiError

_BOOKING = re.compile(r"^/bookings/([A-Za-z0-9_-]{1,64})$")
_CHECK_IN = re.compile(r"^/bookings/([A-Za-z0-9_-]{1,64})/check-in$")


def dispatch(service, method, path, query, body, user_id):
    """method: 'GET'/'POST'/'DELETE'; path like '/rooms' (an '/api' prefix is stripped);
    query: dict of str -> str; body: parsed JSON (dict) or None."""
    try:
        path = path[4:] if path.startswith("/api/") else path
        path = path.rstrip("/") or "/"
        query = query or {}

        if user_id is None:
            raise ApiError(401, "not_signed_in", "Please sign in to continue.")

        if path == "/admin/rooms" and method == "GET":
            return 200, service.admin_rooms(user_id)
        if path == "/admin/rooms/create" and method == "POST":
            return 201, service.save_room(user_id, body)
        if path == "/admin/rooms/update" and method == "POST":
            return 200, service.save_room(user_id, body, update=True)
        if path == "/admin/analytics/reservations" and method == "GET":
            return 200, service.reservation_analytics(user_id)
        if path == "/admin/analytics/patterns" and method == "GET":
            return 200, service.demand_patterns(user_id)
        if path == "/rooms" and method == "GET":
            return 200, service.list_rooms()
        if path == "/users" and method == "GET":
            return 200, service.list_users(user_id)
        if path == "/availability" and method == "GET":
            return 200, service.availability(query.get("room_id"), query.get("date"))
        if path == "/my-bookings" and method == "GET":
            return 200, service.my_bookings(user_id)
        if path == "/all-bookings" and method == "GET":
            return 200, service.all_bookings(user_id)
        if path == "/bookings" and method == "POST":
            return 201, service.create_booking(user_id, body)

        m = _BOOKING.match(path)
        if m and method == "DELETE":
            return 200, service.cancel_booking(user_id, m.group(1))
        m = _CHECK_IN.match(path)
        if m and method == "POST":
            return 200, service.check_in(user_id, m.group(1))

        raise ApiError(404, "route_not_found", "Not found.")
    except ApiError as e:
        return e.status, e.to_body()