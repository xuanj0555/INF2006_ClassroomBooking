# Roomly Security Test Evidence

## Objective

Verify that the deployed AWS API rejects unauthenticated access,
restricts administrative room operations, and prevents a student
from cancelling another organiser’s booking.

## Environment

- Application: Roomly
- Region: us-east-1
- API Gateway: roomly-api
- API base URL: https://kw67yao8v7.execute-api.us-east-1.amazonaws.com
- Authentication: Amazon Cognito
- JWT authorizer: roomly-cognito
- Frontend: http://127.0.0.1:8766/
- Test tool: Chrome Developer Tools Console

Authenticated requests used the signed-in user’s token through
`roomlyAuth.token()`. Token values are excluded from this evidence.

## Results Summary

| Test | Date | Expected | Actual | Result |
|---|---|---|---|---|
| Student requests admin room list | 9 October 2026 | 403 | 403 | PASS |
| No-token request for admin room list | 9 October 2026 | 401 | 401 | PASS |
| Administrator requests admin room list | 9 October 2026 | 200 | 200 | PASS |
| Student attempts room creation | 10 October 2026 | 403 | 403 | PASS |
| Student attempts room update | 10 October 2026 | 403 | 403 | PASS |
| Student attempts another organiser’s cancellation | 10 October 2026 | 403 | 403 | PASS |
| Booking remains confirmed after rejected cancellation | 10 October 2026 | Confirmed | Confirmed | PASS |

## 1. Administrative Room-List Access

### Objective

Verify that only administrators can access the administrative
room-list endpoint.

### Setup

Date: 9 October 2026  
Endpoint: `GET /admin/rooms`

Accounts:
- Test Student B
- Test Admin

### Procedure

1. Sign in as Test Student B.
2. Request the endpoint using the student’s token.
3. Request the endpoint without an Authorization header.
4. Sign in as Test Admin.
5. Request the endpoint using the administrator’s token.
6. Record the returned statuses and response bodies.

### Expected and Actual Results

| Request | Expected status | Actual status | Response |
|---|---|---|---|
| Test Student B | 403 | 403 | Administrator access required |
| No token | 401 | 401 | Unauthorized |
| Test Admin | 200 | 200 | Room data returned |

Student response:

```json
{"code":"not_allowed","message":"Administrator access required."}
```

No-token response:

```json
{"message":"Unauthorized"}
```

### Evidence

- `evidence/security-student-no-token-2026-10-09.png`
- `evidence/security-admin-2026-10-09.png`

### Result

PASS. The endpoint rejected unauthenticated requests and student
access while allowing administrator access.

## 2. Student Room-Creation Rejection

### Objective

Verify that a student cannot bypass the interface and create
a room through a direct API request.

### Setup

Date: 10 October 2026  
Account: Test Student B  
Endpoint: `POST /admin/rooms/create`

### Procedure

1. Sign in as Test Student B.
2. Send an authenticated POST request with
   `Content-Type: application/json`.
3. Submit the following request body:

```json
{
  "room_id": "R999",
  "name": "Security Test Room",
  "capacity": 4,
  "location": "Test Location",
  "is_active": false
}
```

4. Record the returned status and response.

### Expected Result

HTTP 403 with an administrator-access-required message.

### Actual Result

HTTP 403.

```json
{"code":"not_allowed","message":"Administrator access required."}
```

An initial request without `room_id` returned HTTP 400:

```json
{"code":"invalid_input","message":"Invalid room ID."}
```

The initial response demonstrated input validation rather than
administrator authorisation. After supplying `room_id`, the
revised request returned HTTP 403.

### Evidence

- `evidence/security-student-create.png`

### Result

PASS. The revised student request was rejected by the
administrator permission check.

## 3. Student Room-Update Rejection

### Objective

Verify that a student cannot edit a room through a direct API
request.

### Setup

Date: 10 October 2026  
Account: Test Student B  
Room: R001  
Endpoint: `POST /admin/rooms/update`

### Procedure

1. Sign in as Test Student B.
2. Request `GET /rooms` using the student’s token.
3. Find R001 in the returned room list.
4. Submit R001’s existing `room_id`, `name`, `capacity`,
   `location` and `is_active` values to the update endpoint.
5. Record the returned status and response.

Existing values were submitted to avoid changing room contents
if the permission check unexpectedly allowed the request.

### Expected Result

HTTP 403 with an administrator-access-required message.

### Actual Result

HTTP 403.

```json
{"code":"not_allowed","message":"Administrator access required."}
```

### Evidence

- `evidence/security-student-update.png`

### Result

PASS. The student request was rejected by the administrator
permission check.

## 4. Unauthorised Cancellation and Booking Preservation

### Objective

Verify that a student cannot cancel another organiser’s booking
and that the rejected request leaves the booking confirmed.

### Setup

Date: 10 October 2026  
Booking organiser: Test Student A  
Account making cancellation request: Test Student B  
Booking reference: `B5D7DDA38591B08DD6DD12665`  
Room: Study Room A  
Booking time: 11 October 2026, 10:00–11:00, Singapore time  
Participants: Test Student A only

Endpoint:

```text
DELETE /bookings/B5D7DDA38591B08DD6DD12665
```

### Procedure

1. Sign in as Test Student A.
2. Create a future booking without adding Student B.
3. Record the booking reference.
4. Sign out and sign in as Test Student B.
5. Send the following request through Chrome Console:

```javascript
(async () => {
  const response = await fetch(
    'https://kw67yao8v7.execute-api.us-east-1.amazonaws.com/bookings/B5D7DDA38591B08DD6DD12665',
    {
      method: 'DELETE',
      headers: {
        Authorization: 'Bearer ' + roomlyAuth.token()
      }
    }
  );

  console.log('Unauthorised cancellation:', response.status);
  console.log(await response.text());
})();
```

6. Record the returned status and response.
7. Sign back in as Test Student A.
8. Open My bookings and locate the same booking reference.
9. Confirm that its displayed status remains Confirmed.

### Expected Result

HTTP 403. The same booking remains confirmed in the organiser’s
booking view.

### Actual Result

HTTP 403.

```json
{"code":"not_allowed","message":"Only the organiser or administrator can cancel."}
```

The subsequent organiser view showed:

- Reference: `B5D7DDA38591B08DD6DD12665`
- Room: Study Room A
- Date and time: 11 October, 10:00 am
- Organiser: Test Student A
- Members: Test Student A
- Status: Confirmed

### Evidence

- `evidence/security-cancel-denied.png`
- `evidence/security-booking-still-confirmed.png`

### Result

Permission rejection: PASS.  
Booking preservation: PASS.

## Threats Tested

| Threat | Tested control | Outcome |
|---|---|---|
| Unauthenticated access to admin room list | JWT authentication | No-token request rejected with 401 |
| Student bypasses interface to list admin rooms | Backend administrator check | Rejected with 403 |
| Student bypasses interface to create a room | Backend administrator check | Rejected with 403 |
| Student bypasses interface to edit a room | Backend administrator check | Rejected with 403 |
| Student cancels another organiser’s booking | Backend ownership/admin check | Rejected with 403; booking remained confirmed |

## Limitations

- Results apply to the listed endpoints, accounts and requests.
- These tests do not establish security of every API route.
- The successful administrator test covers room listing, not
  administrator room creation or update.
- Analytics permissions, anonymous S3 object access and booking
  conflict prevention are not evaluated in this record.
- These results do not establish IAM least privilege.
- Evidence files must be included at the listed paths.
- Screenshots must be reviewed for sensitive information before
  submission.

## Conclusion

The tested API rejected unauthenticated administrative room-list
access and denied student room-list, creation and update requests.
Administrator room-list access succeeded.

Student B’s attempt to cancel Student A’s booking returned HTTP 403.
The organiser’s booking view subsequently showed the same booking
reference as Confirmed.

All recorded access-control checks passed for the tested operations.
These results demonstrate server-side permission enforcement beyond
hiding interface elements. They do not establish security of every
API route or IAM least privilege.
