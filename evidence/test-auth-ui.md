# Sign-in test (Cognito, frontend)

Tester: Sharlene (Member 1)
Date: 10 October 2026
Browser / version: Google Chrome 155.0.8059.39 (64-bit), Windows 11 25H2, Incognito window, one tab
Site: http://127.0.0.1:8766/ (started with `py -m http.server 8766 --bind 127.0.0.1 --directory src/frontend`)

Objective: confirm that a normal sign-in no longer shows
"Sign-in returned from a different or older attempt", for a student and
an admin, including sign-out followed by a second sign-in.

Accounts: Student A, Student B (non-admin), Admin (see the team's private credential sheet; do not paste passwords or tokens here).

## Steps and results

| # | Step | Expected result | Actual result | Pass/Fail |
|---|---|---|---|---|
| 1 | Open the site in a new Incognito window | Sign-in dialog opens; no error shown | Sign-in dialog was shown on first load; no error message | Pass |
| 2 | Click Sign in, enter Student A credentials on the Cognito page | Return to Roomly; student's name and Sign out shown; no error toast | Return to Roomly; student's name (Student A) and Sign out shown; no error toast | Pass |
| 3 | Confirm the tabs shown | Find a room and My bookings only; no Admin tab | Tabs shown: Find a room, My bookings. No Admin tab | Pass |
| 4 | Click Sign out | Return to Roomly with the Sign-in dialog; no name shown | Return to Roomly with the Sign-in dialog; no name shown  | Pass |
| 5 | Sign in again as Student A (same window) | Succeeds first time; no "different or older attempt" error | Signed in on the first attempt; no error message appeared  | Pass |
| 6 | Sign out, then sign in as Admin | Succeeds; Admin tab visible | Succeeds; Admin tab visible | Pass |
| 7 | Reload the page while signed in | Still signed in (token kept for the tab session) | Still signed in as Admin (token kept for the tab session) | Pass |
| 8 | Sign out, then sign in as Student C | Succeeds; no error | Succeeds; signed in as Student C and no error  | Pass |
| 9 | Repeat steps 4 and 5 three more times | No repeated error | Repeated sign-out and sign-in 3 more times as Student A; no error appeared  | Pass |


## Result

Overall: Pass
Limitations: Tested only in Google Chrome on Windows 11, in one tab, with one sign-in at a time Signing in from several tabs at once was not tested. This test covers the frontend sign-in only
