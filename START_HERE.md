# Combined Roomly project

## Run on your Mac
1. Extract roomly-combined.zip to a NEW folder. Keep your original project as a backup.
2. Open Terminal, type `cd ` (including the space), drag the extracted `roomly-combined` folder into Terminal, and press Enter.
3. Run:

```sh
python3 src/backend/server.py
```

4. Keep Terminal open. Visit http://127.0.0.1:8765/ in your browser.
5. Select Alex Tan for a student or Casey Ng for the administrator (the account menu shows the actual seeded names).

Use this Python application server, not `python3 -m http.server`: the website needs its /api routes.
If port 8765 is already occupied, stop the old server with Control+C in its Terminal before starting this one.
A fresh `roomly.sqlite3` is created automatically. The first run imports the historical CSV into a separate analytics table.

## Check the combined workflow
- Sign in as a student, select tomorrow and a room/time, add another participant, and confirm.
- Switch to that participant: their My bookings should contain the shared booking.
- Try a conflicting reservation: the server must reject it.
- Switch to the organiser and cancel the booking.
- Switch to the administrator: edit/add a room, then view Reservation analytics and Demand patterns.
- Reload and confirm room changes persist.

## Automated checks
```sh
python3 -m unittest discover -s tests -v
```
51 tests passed during combination. JavaScript passed Node syntax checking. The local server could not be started in the assistant sandbox because opening a listening socket was blocked; browser testing remains to be done on your Mac.

## What this package is
This combines the local main booking backend (including participants, transactions and conflict checks) with the frontend branch's admin screens, room editing and historical analytics. It uses local SQLite and demo account selection. It does NOT complete AWS deployment or real authentication. Historical demand counts are not a trained ML forecast.
See MERGE_NOTES.md for exact sources and GitHub merge guidance.
