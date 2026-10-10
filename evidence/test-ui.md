# Interface test matrix

Tester: Sharlene (Member 1)
Date: 10 October 2026
Site: http://127.0.0.1:8766/ against the shared AWS backend
Accounts: Student A, Student B, Admin

"Expected" is what the user guide and the frontend code say should happen.
"Actual" must be filled in from what you saw during the run. Rows marked
"code review" show what the source suggests; they are not test results until you run them.

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
| B6 | Occupied slot | Record exactly what was shown, for example "The 10:00 and 12:00 buttons for R001 were greyed out and could not be clicked" | The R001 10:00 and 12:00 slot buttons were greyed out with strikethrough and could not be clicked | Pass |

## C. Room management (Admin)

| # | Check | Expected | Actual | Pass/Fail |
|---|---|---|---|---|
| C1 | Room ID generated automatically | Add room: ID field is empty with the hint "Assigned when saved"; after saving, a new ID appears in the list | The Room ID field was empty with "Assigned when saved". Clicking Add room with name "Study Room G", capacity 4, location "Level 3 · East wing" showed a newID(R007) room was added. | Pass |
| C2 | Room ID cannot be edited | Field is read-only both when adding and when editing; try typing in it | The Room ID field couldn’t be typed in, either when adding or when editing | Pass |
| C3 | Amenities absent | No amenities field in the form or the list | No amenities field in the room form or the room list | Pass |
| C4 | Edit and save a room | List updates after save; value still there after reload |After editing and saving a room, the list updated, and the change was still there after reloading | Pass |

## D. Cancellation and check-in

| # | Check | Expected | Actual | Pass/Fail |
|---|---|---|---|---|
| D1 | Cancellation updates availability | Booking shows cancelled; the slot is clickable again in Find a room | After cancelling a future booking from My bookings, then a room for the same date and time slot is clickable again | Pass |
| D2 | Check-in success | Check in shown 16:00-16:15 for a 16:00 booking; success message appears; badge becomes "checked in" | success message appears; badge becomes "checked in" | Pass |

## E. Loading, empty and error states

| # | Check | Expected | Actual | Pass/Fail |
|---|---|---|---|---|
| E1 | Loading | Analytics and Demand patterns show "Loading..." text. Record whether Find a room shows anything while loading (code review: it does not) | Reservation analytics showed "Loading results from AWS…" and Demand patterns showed "Loading historical demand patterns from AWS…" while loading. Find a room showed no loading message; the room area stayed empty until the rooms appeared | Partial Pass |
| E2 | Empty bookings | "Your next session starts here" message | An account with no bookings will show the message "Your next session starts here" in My booking| Pass |
| E3 | Empty room results | Choose Group size 8 and record what appears (code review: the count reads "n rooms" with no explanatory message when n is 0) | With Group size set to 8, Find a room showed the heading "Choose your space" and the text "0 rooms". No message explained that no rooms fit the group size or suggested trying a smaller group. | Partial Pass |
| E4 | Expired session | Message "Your sign-in has expired or was rejected" and the sign-in dialog | Not tested. A real token expiry takes about an hour and a rejected token could only be simulated by editing the stored token in DevTools | Not tested |
| E5 | Analytics failure | "Could not load analytics: ..." with source label "AWS analytics unavailable" | Not tested. Setting the browser Offline made Chrome show its own "no internet" page when the page was reloaded, so Roomly's analytics message could not be observed. Blocking the API domain was not tried. | Not tested |

## F. Layout (desktop about 1440 px, narrow about 390 px)

Use DevTools device mode. The stylesheet has breakpoints at 700 px and 480 px.

| # | Area | Desktop | Narrow | Notes / limitations |
|---|---|---|---|---|
| F1 | Participant checkboxes | Names fully visible, checkboxes easy to tick, nothing cut off at the edge | Names fully visible, nothing cut off | None |
| F2 | Room-management inputs | Room ID, Name, Capacity and Location fit inside the card | Fields fit inside the card with no overflow to the right | None |
| F3 | Error toast and login error | Toast message readable and not cut off | Toast message readable | No login error appeared to inspect |
| F4 | Analytics charts (meters) | Bars and labels readable | Bars and labels fit; the page does not scroll sideways | Reservation analytics and Demand patterns both checked |
| F5 | Slot buttons and room cards | Room cards and slot buttons fit; nothing overlaps or is squashed | Same: cards and slot buttons fit, nothing overlaps or is squashed | None |

## Conclusion

Passed: 22 of 26 rows. 
Partial passed: E1, E3. 
Not tested: E4, E5
Limitations: Find a room shows no loading message, and an empty result shows only "0 rooms" with no explanation. The expired-session message (E4) and the analytics failure message (E5) were not observed. Tested only in Google Chrome 155 on Windows 11, with the narrow layout checked at 480 px.
