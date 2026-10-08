# Roomly Booking Rules

## 1. Booking Time Rules

- Rooms use fixed one-hour booking slots.
- Operating hours are 09:00–18:00, Asia/Singapore.
- Each booking reserves one room for one one-hour slot.
- The booking start time must be on the hour.
- Bookings must be made for a future time.
- The final available slot is 17:00–18:00.
- A booking cannot be created for a past or currently active slot.

---

## 2. User Rules

- Only signed-in users can create bookings.
- The booking organiser is determined from the authenticated user identity.
- The browser must not be trusted to choose the organiser.
- Only active users can create or participate in bookings.
- Students can have at most two future confirmed bookings as organisers.
- Staff/faculty permissions are handled separately from normal student
  booking permissions.

---

## 3. Participant Rules

- A booking may contain an organiser and additional participants.
- The organiser is automatically included as a participant.
- The organiser must not be entered again as a participant.
- Duplicate participant IDs are rejected.
- Every selected participant must exist.
- Every selected participant must be active.
- Every participant, including the organiser, can belong to only one active
  booking for a particular time slot.
- A participant cannot be added to a booking if they are already reserved
  in another confirmed booking for the same slot.
- Participant conflicts are checked by the backend and not only by the
  frontend.

---

## 4. Room Rules

- A booking can only use an existing room.
- The room must be active.
- A room can have only one confirmed booking for a particular time slot.
- An inactive room cannot be booked.
- The number of people in a booking cannot exceed the room capacity.

The number of people is:

    organiser + selected participants

For example, a room with capacity 4 can contain:

    1 organiser + 3 participants

but not:

    1 organiser + 4 participants

---

## 5. Booking Creation

When a booking is submitted, the backend performs the following checks:

1. Confirm that the user is authenticated.
2. Determine the organiser from the authenticated identity.
3. Validate the room ID.
4. Confirm that the room exists.
5. Confirm that the room is active.
6. Validate the requested start time.
7. Confirm that the start time is in the future.
8. Confirm that the time is within operating hours.
9. Confirm that the slot is exactly one hour.
10. Validate all participant IDs.
11. Reject duplicate participants.
12. Reject unknown participants.
13. Reject inactive participants.
14. Automatically include the organiser.
15. Check room capacity.
16. Check the organiser's future booking limit.
17. Check whether the room is already booked.
18. Check whether any participant is already booked during the slot.
19. Save the booking and participant reservations in one transaction.

If any validation fails, the booking must not be partially saved.

---

## 6. Transaction Rules

The booking record and participant reservation records must be created
atomically.

If any part of the booking operation fails:

- The booking is not created.
- No participant reservation is created.
- No partial data remains in the database.

The local SQLite implementation uses a write transaction.

Database-level unique indexes provide an additional protection layer against
duplicate room and participant reservations.

---

## 7. Cancellation Rules

- A booking can only be cancelled by its organiser or an authorised
  administrator.
- A participant cannot cancel the entire group booking.
- A user cannot cancel another user's booking.
- A booking that has already started cannot be cancelled.
- Cancelled bookings remain in the database for record keeping.
- Cancellation changes the booking status to `cancelled`.
- Cancellation releases the room reservation.
- Cancellation releases all participant reservations.
- Cancelled bookings do not count as no-shows.

---

## 8. Attendance Rules

- A confirmed booking initially has `pending` attendance.
- Participants can check in from the booking start time.
- The check-in window remains open for 15 minutes after the booking starts.
- A successful check-in records the participant as `attended`.
- If the check-in window closes without attendance, the participant is
  recorded as `no_show`.
- Cancelled bookings are recorded as `not_applicable`.
- A cancelled booking is never counted as a no-show.

---

## 9. Conflict Rules

### Room conflict

Two confirmed bookings cannot use the same room at the same time.

### Participant conflict

A participant cannot belong to two confirmed bookings at the same time.

### Capacity conflict

The organiser plus all participants cannot exceed the room capacity.

### Organiser limit

An organiser cannot exceed two future confirmed bookings.

---

## 10. Security Rules

- Authentication must be enforced by the backend.
- The backend must determine the organiser from the authenticated identity.
- Client-supplied organiser IDs must not be trusted.
- Client-supplied booking status must not be trusted.
- Booking ownership must be checked before cancellation.
- Administrator privileges must be checked separately.
- All input must be validated server-side.
- Frontend validation is not considered a security control.

---

## 11. Error Behaviour

The backend uses the following general status codes:

| HTTP Status | Meaning |
|---|---|
| 200 | Successful request |
| 201 | Booking successfully created |
| 400 | Invalid request or booking rule violation |
| 401 | User is not authenticated |
| 403 | User is authenticated but not authorised |
| 404 | Requested resource does not exist |
| 409 | Booking conflict or booking limit |

---

## 12. Local Prototype and Cloud Deployment

The local prototype uses:

    Browser
       ↓
    Python HTTP server
       ↓
    API layer
       ↓
    BookingService
       ↓
    SQLite

The intended cloud architecture uses:

    Website
       ↓
    API Gateway
       ↓
    AWS Lambda
       ↓
    DynamoDB

The booking rules must remain consistent when the backend is moved from
the local prototype to AWS.