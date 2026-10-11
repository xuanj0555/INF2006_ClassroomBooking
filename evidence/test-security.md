# Security tests

## Objective

Verify that the deployed Roomly API rejects unauthenticated requests,
restricts administrator operations, prevents unauthorised cancellation,
and protects private booking information.

## Test environment

- AWS region: `us-east-1`
- API base URL: `https://kw67yao8v7.execute-api.us-east-1.amazonaws.com`
- Frontend URL: `http://127.0.0.1:8766/`
- Accounts: Test Student A, Test Student B and Test Admin
- Tool: Chrome Developer Tools Console
- Authentication: Cognito login token supplied through the Authorization
  header, except in tests explicitly performed without a token.

Requests were sent directly to the API. These tests check backend
responses rather than relying only on hidden buttons or disabled
interface controls.

## Results summary

| Test | Date | Expected result | Actual result | Result |
|---|---|---|---|---|
| Student requests admin room list | 9 October 2026 | 403 | 403 | Pass |
| No-token request to admin room list | 9 October 2026 | 401 | 401 | Pass |
| Administrator requests admin room list | 9 October 2026 | 200 | 200 | Pass |
| Student attempts room creation | 10 October 2026 | 403 | 403 | Pass |
| Student attempts room update | 10 October 2026 | 403 | 403 | Pass |
| Student attempts cancellation of another organiser's booking | 10 October 2026 | 403 | 403 | Pass |
| Booking remains confirmed after rejected cancellation | 10 October 2026 | Booking remains confirmed | Same booking displayed as Confirmed | Pass |
| Student B requests own booking list | 10 October 2026 | 200; Student A's private booking excluded | 200; private booking absent | Pass |
| No-token request to analytics before permission update | 10 October 2026 | 401 | 401 | Pass |
| Administrator requests analytics before permission update | 10 October 2026 | 200 with analytics data | 200 with historical analytics data | Pass |
| Student requests analytics after permission update | 11 October 2026 | 403 | 403 | Pass |
| Administrator requests analytics after permission update | 11 October 2026 | 200 with analytics data | 200 with historical analytics data | Pass |

## 1. Admin room-list access

Date: 9 October 2026  
Endpoint and method: `GET /admin/rooms`  
Objective: Verify that the admin room list is accessible to an
administrator and denied to students and unauthenticated callers.  
Request body: None.

### Steps

1. Sign in as Test Student B and request the endpoint using the
   account's login token.
2. Request the endpoint without an Authorization header.
3. Sign in as Test Admin and request the endpoint using its login token.
4. Compare the returned HTTP statuses and response bodies.

### Expected and actual results

| Account | Expected status | Actual status | Result |
|---|---|---|---|
| Test Student B | 403 | 403 | Pass |
| No token | 401 | 401 | Pass |
| Test Admin | 200 | 200 | Pass |

Observed responses:

- Student: `{"code":"not_allowed","message":"Administrator access required."}`
- No token: `{"message":"Unauthorized"}`
- Administrator: Room data returned successfully.

### Evidence

- `security-student-no-token-2026-10-09.png`
- `security-admin-2026-10-09.png`

### Interpretation

The deployed endpoint rejected unauthenticated requests and denied
student access while allowing administrator access.

## 2. Student room-creation rejection

Date: 10 October 2026  
Account/role: Test Student B — student  
Endpoint and method: `POST /admin/rooms/create`  
Objective: Verify that a student cannot create a room through a
direct API request.

### Request body

```json
{
  "room_id": "R999",
  "name": "Security Test Room",
  "capacity": 4,
  "location": "Test Location",
  "is_active": false
}
```

### Steps

1. Sign in as Test Student B.
2. Send a direct POST request with the student's login token,
   JSON content type and the request body above.
3. Record the HTTP status and response.

### Expected result

HTTP 403 with an administrator-access rejection.

### Actual result

HTTP 403:

```json
{
  "code": "not_allowed",
  "message": "Administrator access required."
}
```

Result: Pass.

### Initial attempt

An earlier request omitted `room_id` and returned HTTP 400:

```json
{
  "code": "invalid_input",
  "message": "Invalid room ID."
}
```

That response demonstrated input validation and was not counted as
a successful authorisation test. The corrected request returned
the expected HTTP 403.

This records the deployed version tested on 10 October. Subsequent
automatic room-ID assignment is documented separately in the
deployment record.

### Evidence

- `security-student-create.png`

### Interpretation

The deployed endpoint rejected the student's room-creation request
with an explicit administrator-access error.

## 3. Student room-update rejection

Date: 10 October 2026  
Account/role: Test Student B — student  
Endpoint and method: `POST /admin/rooms/update`  
Objective: Verify that a student cannot update an existing room
through a direct API request.

### Request body

The test retrieved room `R001` from `GET /rooms` and submitted
its existing values for:

- `room_id`
- `name`
- `capacity`
- `location`
- `is_active`

Using the existing values supplied a valid room-update request
without intentionally changing the room's information.

### Steps

1. Sign in as Test Student B.
2. Request the room list and locate `R001`.
3. Send the room's existing fields to the update endpoint using
   the student's login token.
4. Record the HTTP status and response.

### Expected result

HTTP 403 with an administrator-access rejection.

### Actual result

HTTP 403:

```json
{
  "code": "not_allowed",
  "message": "Administrator access required."
}
```

Result: Pass.

### Evidence

- `security-student-update.png`

### Interpretation

The deployed endpoint rejected the student's room-update request.
This checks authorisation; it does not demonstrate a successful
administrator update.

## 4. Unauthorised cancellation and booking preservation

Date: 10 October 2026  
Requesting account/role: Test Student B — student, not the booking organiser  
Endpoint and method: `DELETE /bookings/B5D7DDA38591B08DD6DD12665`  
Objective: Verify that Student B cannot cancel Student A's booking
and that the rejected request leaves the booking confirmed.  
Request body: None.

### Test booking

- Booking reference: `B5D7DDA38591B08DD6DD12665`
- Room: Study Room A
- Date: 11 October 2026
- Time: 10:00–11:00, Singapore time
- Organiser: Test Student A
- Members: Test Student A only

### Steps

1. Create the future booking as Test Student A without adding Student B.
2. Sign in as Test Student B.
3. Send a direct cancellation request for the booking reference
   using Student B's login token.
4. Record the HTTP status and response.
5. Return to Test Student A's My bookings view.
6. Locate the same booking reference and inspect its status.

### Expected result

- Student B receives HTTP 403.
- The booking remains confirmed.

### Actual result

The cancellation request returned HTTP 403:

```json
{
  "code": "not_allowed",
  "message": "Only the organiser or administrator can cancel."
}
```

The subsequent organiser-view screenshot shows the same booking
reference with status `Confirmed`.

Result: Pass for cancellation rejection and booking preservation.

### Evidence

- `security-cancel-denied.png`
- `security-booking-still-confirmed.png`

### Interpretation

The backend rejected cancellation by a student who was not the
organiser. The subsequent booking view confirms that the tested
booking remained confirmed.

## 5. Private booking exclusion from Student B's booking list

Date: 10 October 2026  
Account/role: Test Student B — student  
Endpoint and method: `GET /my-bookings`  
Objective: Verify that Student A's private booking is excluded
from Student B's booking-list response.  
Request body: None.

### Test booking

Booking reference: `B5D7DDA38591B08DD6DD12665`

Student A is the organiser and sole member. Student B is not a
member of this booking.

### Steps

1. Sign in as Test Student B.
2. Request `/my-bookings` using Student B's login token.
3. Record the HTTP status and response.
4. Search the response for the private booking reference.

### Expected result

HTTP 200, with Student A's private booking absent from the response.

Bookings organised by Student B or shared with Student B may
legitimately appear.

### Actual result

- HTTP status: 200
- Console result: `Student A private booking present: false`
- The tested private booking reference was absent from the response.

Result: Pass.

### Evidence

- `security-booking-privacy.png`

### Interpretation

The tested private booking was excluded from Student B's booking
list. This checks one known private booking; it does not establish
privacy across every endpoint or every possible request.

## 6. Analytics access without a token before the permission update

Date: 10 October 2026  
Account/role: Unauthenticated API request  
Endpoint and method: `GET /analytics`  
Objective: Verify that the analytics endpoint rejects a request
without an authentication token.  
Request body: None.

### Steps

1. Send a direct request to `/analytics` without an Authorization header.
2. Record the HTTP status and response.

The browser displayed a signed-in student session, but this test
request deliberately omitted the token.

### Expected result

HTTP 401 without analytics data.

### Actual result

HTTP 401:

```json
{
  "message": "Unauthorized"
}
```

Result: Pass.

### Evidence

- `security-analytics-no-token.png`

### Interpretation

The deployed analytics endpoint rejected the no-token request.
This demonstrates authentication enforcement for the version
tested before the permission update. It does not independently
establish administrator-only access.

## 7. Administrator analytics access before the permission update

Date: 10 October 2026  
Account/role: Test Admin — administrator  
Endpoint and method: `GET /analytics`  
Objective: Verify that an authenticated administrator could retrieve
historical analytics before the subsequent permission update.  
Request body: None.

### Steps

1. Sign in as Test Admin.
2. Request `/analytics` using the administrator's login token.
3. Record the HTTP status and inspect the returned data.

### Expected result

HTTP 200 with historical analytics data.

### Actual result

HTTP 200 with a JSON response containing:

- A source description identifying a historical reservation dataset
  separate from live bookings.
- Summary metrics.
- Reservations grouped by room.
- Reservations grouped by weekday.
- Reservations grouped by start hour.

Visible summary values included:

- Record count: 51,319
- Room count: 46
- Average duration: 95.43 minutes
- Median duration: 90 minutes
- Total reserved hours: 81,622.72

Result: Pass for the version tested on 10 October 2026.

### Evidence

- `security-analytics-admin.png`

### Interpretation

An authenticated administrator successfully retrieved historical
analytics before the permission update. This result does not
establish administrator access after that update or independently
validate the analytics calculations.

## 8. Student analytics rejection after the permission update

Date: 11 October 2026  
Account/role: Test Student B — student  
Endpoint and method: `GET /analytics`  
Request body: None.

### Objective

Verify that the updated analytics backend rejects a student request
containing a valid authentication token.

### Steps

1. Sign in as Test Student B.
2. Request `/analytics` using the student's login token.
3. Record the HTTP status and response.

### Expected result

HTTP 403 without historical analytics data.

### Actual result

The request returned HTTP 403.

Result: Pass.

### Evidence

- `security-analytics-student.png`

### Interpretation

The tested student account was denied access after the backend
permission update. This verifies the tested request and account;
it does not establish the outcome for every possible account.

## 9. Administrator analytics retest after the permission update

Date: 11 October 2026  
Account/role: Test Admin — administrator  
Endpoint and method: `GET /analytics`  
Request body: None.

### Objective

Verify that an administrator can still retrieve historical
analytics after the backend permission update.

### Steps

1. Sign in as Test Admin.
2. Request `/analytics` using the administrator's login token.
3. Record the HTTP status and response.
4. Save the supporting screenshot.

### Expected result

HTTP 200 with historical analytics JSON.

### Actual result

HTTP 200 with historical analytics JSON.

The console displayed:

`Admin analytics after update: 200`

Visible summary values included:

- Record count: 51,319
- Room count: 46
- Average duration: 95.43 minutes
- Median duration: 90 minutes
- Total reserved hours: 81,622.72

Result: Pass.

### Evidence

- `security-analytics-admin-after-update.png`

### Interpretation

The tested administrator account successfully retrieved historical
analytics after the permission update. Together with Test 8's
student HTTP 403 result, this supports role enforcement for the
tested accounts. It does not independently validate the calculations.
## Threats covered

| Threat | Observed protection | Supporting tests |
|---|---|---|
| Unauthenticated access to admin room data | No-token request rejected with 401 | Test 1 |
| Student accesses administrator room operations | Student requests rejected with 403 | Tests 1–3 |
| Student cancels another organiser's booking | Cancellation rejected with 403; booking remains confirmed | Test 4 |
| Student views another user's private booking | Tested private booking excluded from the student's booking-list response | Test 5 |
| Unauthenticated access to historical analytics | No-token request rejected with 401 before the permission update | Test 6 |
| Student retrieves administrator analytics | Tested student request rejected with 403 after the permission update | Test 8 |

## Scope and limitations

- Results apply to the tested endpoints, accounts, requests and
  deployed versions.
- After the permission update, the tested student account received
  HTTP 403 and the tested administrator account received HTTP 200
  with historical analytics data on 11 October 2026.
- The no-token analytics test and the earlier administrator
  analytics test were performed before the permission update.
- Successful administrator room creation and updating are not
  demonstrated by these rejection tests. Separate functional,
  interface and deployment records cover those operations.
- Booking privacy was checked using one known private booking.
- Room conflicts, participant conflicts, anonymous S3 access and
  repository secret checks require separate evidence.
- These tests do not prove least-privilege IAM permissions,
  resistance to every attack, or performance under load.
- Referenced screenshots must be included in the evidence folder.
  Passwords, tokens and AWS credentials must be excluded.

## Conclusion

The completed tests passed their stated expected results. The
deployed API rejected the tested unauthenticated requests, denied
student access to administrator room operations, prevented
unauthorised cancellation, preserved the tested booking, and
excluded Student A's private booking from Student B's booking list.

Administrator analytics access succeeded before the permission
update. After the update, the tested student account was rejected
with HTTP 403 and the administrator successfully retrieved
historical analytics with HTTP 200.
These results support the tested authentication, authorisation
and booking-privacy controls within the documented scope.
