# Interface test matrix

Initial tester: Sharlene (Member 1)  
Initial test date: 10 October 2026  
Additional tester: Shermaine  
Additional test date: 11 October 2026  
Site: http://127.0.0.1:8766/ against the shared AWS backend  
Accounts: Student A, Student B, Student C, Admin

"Expected" is what the user guide and the frontend code say should happen.
"Actual" records what was observed during testing. Source-code observations alone are not test results.

## A. Role-based screens

| # | Check | Expected | Actual | Pass/Fail |
|---|---|---|---|---|
| A1 | Student sees only permitted screens | Find a room, My bookings. No Admin tab, no Staff overview | Signed in as Student A: tabs shown were Find a room and My bookings. No Admin tab | Pass |
| A2 | Student cannot open Admin by other means | Admin content stays hidden (frontend ignores the switch); API calls to `admin/*` return 403 (Member 2 to confirm server-side) | No Admin tab or Admin content was reachable from the student’s page. Server-side rejection is tested by Member 2 | Pass |
| A3 | Admin sees room management | Admin tab > Rooms with the room form and room list | Signed in as Admin: Admin tab shown with a room form and the room list | Pass |
| A4 | Admin sees analytics | Admin tab > Reservation analytics and Demand patterns load | Admin tab showed Reservation analytics and Demand patterns, and both loaded | Pass |

## B. Booking form

| # | Check | Expected | Actual | Pass/Fail |
|---|---|---|---|---|
| B1 | Current organiser automatically included | Booking shows the organiser as a member without ticking anything | The confirmation dialog showed me (the organiser) as already included. I didn’t tick anything | Pass |
| B2 | Participant list excludes the organiser | Own name not offered as a checkbox | My own name wasn’t offered as a checkbox in the participant list | Pass |
| B3 | Participant selection displays correctly | Names in labelled checkboxes; ticked boxes remain ticked until confirm | Participants were listed by name with checkboxes. The two I ticked stayed ticked until I confirmed | Pass |
| B4 | Admin accounts excluded from participant list | Not listed (depends on deployed `/users`; the frontend only removes the current user) | No admin accounts appeared in the participant list | Pass |
| B5 | Booked participant sees the booking | Student C sees it in My bookings | Signed in as Student C: the booking appeared in My bookings with the same room, time and organiser | Pass |
| B6 | Occupied slot | Occupied slot buttons are unavailable | The R001 10:00 and 12:00 slot buttons were greyed out with strikethrough and could not be clicked | Pass |

## C. Room management (Admin)

| # | Check | Expected | Actual | Pass/Fail |
|---|---|---|---|---|
| C1 | Room ID generated automatically | Add room: ID field is empty with the hint "Assigned when saved"; after saving, a new ID appears in the list | The Room ID field was empty with "Assigned when saved". Clicking Add room with name "Study Room G", capacity 4, location "Level 3 · East wing" showed that a new room, R007, was added | Pass |
| C2 | Room ID cannot be edited | Field is read-only both when adding and when editing; try typing in it | The Room ID field couldn’t be typed in, either when adding or when editing | Pass |
| C3 | Amenities absent | No amenities field in the form or the list | No amenities field in the room form or the room list | Pass |
| C4 | Edit and save a room | List updates after save; value still there after reload | After editing and saving a room, the list updated, and the change was still there after reloading | Pass |

## D. Cancellation and check-in

| # | Check | Expected | Actual | Pass/Fail |
|---|---|---|---|---|
| D1 | Cancellation updates availability | Booking shows cancelled; the slot is clickable again in Find a room | After cancelling a future booking from My bookings, the same date and time slot was clickable again in Find a room | Pass |
| D2 | Check-in success | Check in shown 16:00–16:15 for a 16:00 booking; success message appears; badge becomes "checked in" | Success message appeared; badge became "checked in" | Pass |

## E. Loading, empty and error states

| # | Check | Expected | Actual | Pass/Fail |
|---|---|---|---|---|
| E1 | Loading | Analytics and Demand patterns show loading text. Record whether Find a room shows anything while loading | Reservation analytics showed "Loading results from AWS…" and Demand patterns showed "Loading historical demand patterns from AWS…" while loading. Find a room showed no loading message; the room area stayed empty until the rooms appeared | Partial Pass |
| E2 | Empty bookings | "Your next session starts here" message | An account with no bookings showed "Your next session starts here" in My bookings | Pass |
| E3 | Empty room results | Choose Group size 8 and record what appears | With Group size set to 8, Find a room showed "Choose your space" and "0 rooms". No message explained that no rooms fit the group size or suggested trying a smaller group | Partial Pass |
| E4 | Simulated local session expiry | The next request displays the sign-in dialog and "Please sign in to continue." | On 11 October 2026, Shermaine set Student A’s stored login expiry to a past time, then changed the room-search date to trigger a new request. The sign-in dialog appeared with "Please sign in to continue." See [screenshot](ui-session-expiry.png). The separate server HTTP 401 handling path was not tested | Pass — local expiry only |
| E5 | Analytics failure | "Could not load analytics: ..." with source label "AWS analytics unavailable" | Not tested successfully. Setting the browser Offline made Chrome show its own "no internet" page when the page was reloaded, so Roomly’s analytics message could not be observed. No completed analytics request-blocking result has been recorded | Not tested |

## F. Layout (desktop about 1440 px, narrow at 480 px)

The stylesheet has breakpoints at 700 px and 480 px. The recorded narrow-layout checks were performed at 480 px; approximately 390 px was not separately verified.

| # | Area | Desktop | Narrow | Notes / limitations |
|---|---|---|---|---|
| F1 | Participant checkboxes | Names fully visible, checkboxes easy to tick, nothing cut off at the edge | Names fully visible, nothing cut off | None |
| F2 | Room-management inputs | Room ID, Name, Capacity and Location fit inside the card | Fields fit inside the card with no overflow to the right | None |
| F3 | Error toast and login error | Toast message readable and not cut off | Toast message readable | No login error appeared during the original layout checks |
| F4 | Analytics charts (meters) | Bars and labels readable | Bars and labels fit; the page does not scroll sideways | Reservation analytics and Demand patterns both checked |
| F5 | Slot buttons and room cards | Room cards and slot buttons fit; nothing overlaps or is squashed | Same: cards and slot buttons fit, nothing overlaps or is squashed | None |

## Simulated Local Login Expiry

- Test date: 11 October 2026
- Tester: Shermaine
- Environment: Google Chrome on macOS against the shared AWS backend
- Account: Test Student A
- Procedure: While signed in, changed the stored login expiry to a past time in Chrome Console, then changed the room-search date to trigger a new request.
- Expected: The application prompts the user to sign in again.
- Actual: The sign-in dialog appeared with “Please sign in to continue.”
- Result: Pass
- Evidence: [Session-expiry prompt](ui-session-expiry.png)
- Scope: This verifies simulated frontend local-expiry handling. The separate server HTTP 401 response-handling path was not tested.

## Conclusion

The matrix contains 26 rows:

- Passed or satisfactory observations: 23 rows, including E4 for simulated local expiry only.
- Partial Pass: E1 and E3.
- Not tested: E5.

Find a room shows no loading message, and an empty room result shows only "0 rooms" without an explanation. The server HTTP 401 expiry/rejection message and the analytics-failure message remain untested.

The original interface and layout checks were recorded in Google Chrome 155 on Windows 11, with the narrow layout checked at 480 px. The additional simulated local-expiry test was completed in Chrome on macOS on 11 October 2026. The sign-in dialog was observed in that additional test, but its narrow-layout appearance was not separately checked.
