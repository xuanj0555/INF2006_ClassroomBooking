# API Gateway configuration

Recorded on: 10 October 2026
API type: HTTP API
Region: us-east-1
Stage: $default
Automatic deployment: Enabled

| Route | Integration/function | Authorizer |
|---|---|---|
| GET /session | roomly-booking-api | roomly-cognito |
| GET /users | roomly-booking-api | roomly-cognito |
| GET /rooms | roomly-get-rooms | roomly-cognito |
| GET /analytics | roomly-get-analytics | roomly-cognito |
| GET /availability | roomly-booking-api | roomly-cognito |
| GET /my-bookings | roomly-booking-api | roomly-cognito |
| GET /all-bookings | roomly-booking-api | roomly-cognito |
| POST /bookings | roomly-booking-api | roomly-cognito |
| DELETE /bookings/{booking_id} | roomly-booking-api | roomly-cognito |
| POST /bookings/{booking_id}/check-in | roomly-booking-api | roomly-cognito |
| GET /admin/rooms | roomly-booking-api | roomly-cognito |
| POST /admin/rooms/create | roomly-booking-api | roomly-cognito |
| POST /admin/rooms/update | roomly-booking-api | roomly-cognito |

## JWT authorizer

Name: roomly-cognito
Type: JWT
Authorizer ID: mofqpt
Issuer: https://cognito-idp.us-east-1.amazonaws.com/us-east-1_EtQjacsSX
Audience: 7bqthe08cf0fovnaqa43chjec5
Identity source: $request.header.Authorization

## CORS

Allowed origins:
- http://127.0.0.1:8765
- http://localhost:8765
- http://127.0.0.1:8766

Allowed methods:
- GET
- POST
- DELETE
- OPTIONS

Allowed headers:
- content-type
- authorization

Exposed headers: None
Preflight maximum age: 0 seconds
Allow credentials: No
