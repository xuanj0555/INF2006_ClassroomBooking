# Booking workflow test

Date: 9 October 2026
Objective: Verify booking creation, shared participant visibility,
persistence after refresh, cancellation and slot release.

Setup:
- Accounts: Test Student A and Test Student B
- Room: R001 - Study Room A
- Booking date and time: 10 October, 12PM
- Booking reference: B7C79D5AB7CA4228BCB476C5D

| Step | Expected result | Actual result | Pass/Fail |
|---|---|---|---|
| A books with B | Booking succeeds | Booking suceeds | Pass |
| A views booking | Both participants shown | Both participants shown | Pass |
| A refreshes | Booking persists | Booking persists| Pass |
| B views booking | Same booking visible | Same booking visible | Pass |
| Occupied slot checked | Duplicate selection prevented or request rejected | Duplicate selection prevented or request rejected | Pass |
| A cancels | Booking marked cancelled | Booking marked cancelled | Pass |
| Availability checked | Slot available again | Slot available again | Pass |

Evidence:
- functional-booking-created.png
- functional-booking-after-refresh.png
- functional-participant-view.png
- functional-occupied-slot.png
- functional-booking-cancelled.png
- functional-slot-released.png

Conclusion: All tested booking workflow steps passed. Student A successfully
created a booking with Student B, and both users could view it. The booking
persisted after refreshing the page, and the occupied slot could not be
selected again. Cancelling the correct booking marked it as cancelled
and made its slot available for a new booking.
