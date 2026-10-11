# Backend Correctness Test Evidence

## Scope

These tests cover the DynamoDB booking service as well as the local backend.
The DynamoDB tests use a small in-memory mock of the DynamoDB resource and
transaction client. This keeps the tests repeatable and does not require AWS
credentials.

Deployed AWS checks are recorded separately below. Mock tests and deployed API results have different scopes and must not be treated as interchangeable.

## 1. DynamoDB service tests

**Objective:** Verify the actual `DynamoDBService` booking logic and transaction
construction for the main correctness rules.

**Command:**

```text
python -m unittest tests.test_dynamodb_service -v
```

**Expected result:** All DynamoDB service tests pass.

**Actual result (10 October 2026):** 13 tests passed.

The tests cover:

- two requests competing for the same room and slot
- the same participant being requested in different rooms at the same time
- repeated identical booking submission
- room capacity
- organiser future-booking limit
- administrator participant restriction
- cancellation releasing room and participant reservations
- cancellation authorisation
- check-in before, during and after the allowed window
- room-number generation
- concurrent room creation

## 2. Existing local backend tests

**Objective:** Confirm that the existing SQLite backend and admin integration
remain correct after the backend rule changes.

**Command:**

```text
python -m unittest tests.test_backend tests.test_admin -v
```

**Expected result:** All local backend and admin tests pass.

**Actual result (10 October 2026):** 57 tests passed.

## 3. Deployed cloud checks

Test date: 11 October 2026

Tester: Shermaine

Endpoint: `https://kw67yao8v7.execute-api.us-east-1.amazonaws.com/bookings`

Method: `POST` with JSON and a signed-in Cognito account's bearer token. Tokens are not recorded in this evidence.

### Room conflict

With Student A's confirmed R001 booking for 12 October 2026, 10:00–11:00 Singapore time, Student B submitted:

```json
{"room_id":"R001","start_time":"2026-10-12T10:00:00+08:00","participant_ids":[]}
```

Expected: HTTP 409. Actual: HTTP 409, code `booking_conflict`, message `Slot/participant conflict or concurrent change. Refresh and retry.` Result: PASS for rejection of the occupied room-slot request.

Evidence: [Student A's setup booking](studentAbooking.png), [room conflict response](cloud-room-conflict.png).

### Participant conflict

Student B requested R002 for the same time with Student A (`U001`) included as a participant:

```json
{"room_id":"R002","start_time":"2026-10-12T10:00:00+08:00","participant_ids":["U001"]}
```

Expected: HTTP 409. Actual: HTTP 409 with the same `booking_conflict` code and message. Result: PASS for rejection of the conflicting-participant request. The response does not distinguish the specific internal conflict condition.

Evidence: [participant conflict response](cloud-participant-conflict.png).

### Simultaneous identical requests

Signed in as Student A, sent two identical requests for R001 at `2026-10-12T10:00:00+08:00`, with `participant_ids: []`, using `Promise.all([send(1), send(2)])`.

Expected: both requests resolve to the same confirmed booking rather than creating two active bookings. The handler returns HTTP 201 for the existing-booking response as well as for initial creation.

Actual: both requests returned HTTP 201 with booking ID `BEB9E629929A992E520A6C395`. After refreshing My Bookings, the matching reference was displayed as Confirmed for Study Room A, 12 October at 10:00, for one hour. Older cancelled records were retained as history.

Result: PASS for the observed identical-request handling and matching refreshed booking.

Evidence: [both responses](cloud-concurrent-identical-requests.png), [matching confirmed booking after refresh](cloud-concurrent-single-booking.png).

### Other deployed operations

Booking creation/persistence and cancellation/slot release are recorded in [test-functional.md](test-functional.md). Rejection of cancellation by a non-organiser is recorded in [test-security.md](test-security.md).

### Limitations and outstanding checks

- The room and participant conflict requests above were made against an existing booking; they were not simultaneous requests by different organisers.
- Simultaneous competing requests by different users for a free room-slot remain untested on AWS.
- These screenshots do not establish that no partial DynamoDB records were written after rejected requests; that requires a separate persisted-state check.
- This small test does not establish high-load performance or all possible concurrency outcomes.
