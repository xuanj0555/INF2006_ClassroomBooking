# Roomly Backend

## Overview

The Roomly backend contains the core booking logic and validation for the campus room booking service. It manages users, rooms, bookings and booking participants, while enforcing booking rules and preventing conflicting reservations.

The backend booking logic is separated from the local HTTP server startup so that the same logic can also be used by the AWS Lambda deployment.

### Main Backend Components

- `src/backend/bookingService.py` — Core booking logic and booking validation.
- `src/backend/dynamodbService.py` — DynamoDB data access and transactional reservation handling.
- `src/backend/API.py` — HTTP API routes used by the application.
- `src/backend/lambda_handler.py` — AWS Lambda entry point for the deployed backend.
- `src/backend/adminService.py` — Administrator-related backend operations.
- `src/backend/server.py` — Local backend server used for development/testing.

## Booking Validation

When a booking is created, the backend checks the following rules:

1. The organiser and selected participants must exist and be active.
2. The selected room must exist and be active.
3. The booking must be for a valid future one-hour slot.
4. Duplicate participants are rejected.
5. The organiser is automatically included as a participant.
6. Administrator accounts cannot be added as booking participants.
7. The number of participants cannot exceed the room capacity.
8. The organiser's future booking limit is enforced.
9. The room cannot already be booked for the same time slot.
10. Participants cannot be booked in another room at the same time.
11. Booking and reservation records are saved transactionally to maintain consistency.

## Cancellation

Booking cancellation is also handled by the backend.

The backend:

1. Checks that the requester is the booking organiser or an authorised administrator.
2. Retains the cancelled booking record.
3. Releases the associated room reservation.
4. Releases the associated participant reservations.

This allows the cancelled time slot to become available again while preserving the booking history.

## Cloud Data Storage

The deployed backend uses Amazon DynamoDB for persistent data storage.

The main tables are:

- `Rooms` — Stores room information.
- `RoomlyUsers` — Stores user information, including roles and active status.
- `RoomlyBookings` — Stores booking records.
- `RoomlyReservations` — Stores room and participant reservation records used for conflict prevention.

The backend uses DynamoDB transactions and a revision guard to help prevent conflicting updates during concurrent operations.

## Backend Tests

Backend testing covers both the local backend and the DynamoDB service implementation.

### Install Dependencies

From the project root, install the test dependencies:

```bash
python -m pip install -r tests/requirements.txt