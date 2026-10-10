# Backend Correctness Test Evidence

## Scope

These tests cover the DynamoDB booking service as well as the local backend.
The DynamoDB tests use a small in-memory mock of the DynamoDB resource and
transaction client. This keeps the tests repeatable and does not require AWS
credentials.

The deployed AWS check is a separate step and must be completed with Member 3.
It should not be described as a successful cloud test until the deployed
endpoint has been exercised and the result recorded.

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

## 3. Deployed cloud check

**Status:** Pending coordination with Member 3.

The deployed DynamoDB implementation should be tested with a small repeatable
check using the deployed API. Record the command/steps, expected result, actual
result and date here once completed.

Suggested minimum cloud checks:

1. Two users attempt the same room and time slot; only one booking succeeds.
2. The same participant is requested in two different rooms at the same time;
   the second booking is rejected.
3. The organiser cancels a booking; the room and participant become available
   again.
4. A different user attempts to cancel the organiser's booking; the request is
   rejected.
