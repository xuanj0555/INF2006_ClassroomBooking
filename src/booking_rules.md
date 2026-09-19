# Roomly Booking Rules

## 1. Scope

Roomly supports campus room reservations and reservation-demand analytics.

Students and faculty can view room availability, create group bookings
and cancel their reservations. The system enforces room capacity,
booking limits and participant scheduling constraints.

Administrators can analyse historical reservation patterns, including
popular rooms, peak booking periods and reserved hours.

## 2. User access

- Only authenticated, active users may create bookings.
- The backend obtains the organiser's identity from the verified session.
- Users cannot grant themselves faculty or administrator permissions.
- Students and faculty follow the same booking rules unless a different
  policy is explicitly agreed and implemented.

## 3. Room availability

- Only active rooms accept new bookings.
- New bookings must be for a future time.
- Slots run from 09:00 to 18:00 in Asia/Singapore timezone.
- Each booking lasts exactly one hour and starts on the hour.
- The last permitted slot is 17:00–18:00.
- Each room can have only one confirmed booking per slot.

## 4. Participants

- Every booking must include its organiser as a participant.
- All participants must have valid, active user accounts.
- Duplicate participants within a booking are prohibited.
- Participant count, including the organiser, cannot exceed room capacity.
- A user cannot organise or participate in two confirmed bookings
  during the same slot, even in different rooms.
- A user may organise at most two future confirmed bookings.

## 5. Cancellation

- An organiser may cancel their own booking before its start time.
- Other participants cannot cancel the entire booking.
- An explicitly authorised administrator may cancel a future booking.
- Faculty status alone does not grant this administrator permission.
- Cancellation changes status to cancelled; the booking record is retained.
- Cancelled bookings no longer reserve the room or participant slots.

## 6. Conflict prevention

- The backend enforces all rules; frontend validation alone is insufficient.
- Room and participant reservations must be saved atomically.
- If any validation or reservation fails, no partial booking is retained.
- Concurrent requests must not reserve the same room or participant slot.
- Changes to participants must recheck capacity and scheduling conflicts.

## 7. Historical data and analytics

- The Kaggle dataset is separate from live Roomly bookings.
- Historical durations and dates are preserved.
- The application's one-hour booking rule is not imposed retroactively
  on historical records.
- Synthetic accounts or demo records are clearly labelled.
- Analytics must not describe reservations as verified attendance.
