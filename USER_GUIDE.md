# Roomly: teammate setup and user guide

## What is shared

This frontend connects to the team's deployed AWS API. Cognito handles sign-in, API Gateway and Lambda handle requests, and DynamoDB stores current rooms and bookings. Analytics comes from the deployed analytics service.

Pushing to GitHub shares source code; it does not deploy Lambda changes or host the website. Everyone who runs this frontend uses the same AWS data, so coordinate test bookings and room edits. No AWS console login, access keys, or boto3 installation is required to use the frontend.

The configured AWS services must remain available. Ask the AWS owner to check the Learner Lab and resources if cloud requests fail.

## 1. Get the files

Install Python 3 and clone this repository with GitHub Desktop. If already cloned, use Fetch origin and Pull origin to obtain the latest version. Alternatively download the repository ZIP and extract it.

Keep the complete repository structure. Do not open index.html directly or copy only that file. The frontend needs app.js, auth.js, style.css and favicon.svg in the same folder.

## 2. Start the website

Open Terminal or PowerShell in the repository's top-level folder. This is the folder containing README.md and src.

macOS/Linux:

```sh
python3 -m http.server 8766 --bind 127.0.0.1 --directory src/frontend
```

Windows:

```powershell
py -m http.server 8766 --bind 127.0.0.1 --directory src/frontend
```

Leave the terminal running, then open:

http://127.0.0.1:8766/

Use that exact address and port: the Cognito callback and API CORS configuration must allow it. Do not substitute localhost or another port without updating AWS configuration. Each teammate opens this address on their own computer; it is not a publicly hosted website.

Press Ctrl+C in the terminal to stop the server. Restart it with the same command when needed. This static server serves the AWS-connected frontend; it does not start the separate SQLite demo backend.

## 3. Sign in and test accounts

Click Sign in, enter your assigned Cognito username and password on the Amazon Cognito page, and complete any first-login password-change prompt. You should return to Roomly with your display name at the top.

| Application account | Display name | Intended access |
| --- | --- | --- |
| U001 | Test Student A | Find rooms, book, view own bookings and check in |
| U002 | Test Student B | Find rooms, book, view own bookings and check in |
| U003 | Test Admin | Room management, staff overview and analytics |

These are application IDs and display names, not necessarily Cognito login usernames. Obtain the exact Cognito username and password from the project owner through a private channel. Never commit passwords, access tokens, AWS access keys or a filled credential sheet to this repository.

Public self-service registration is not enabled. The AWS owner provisions test accounts and maps each Cognito identity to exactly one active RoomlyUsers record. Admin access is assigned by the owner; users cannot select it during login.

To switch accounts, select Sign out at the top of Roomly, then Sign in with the other account. Sign in again if your session expires.

## 4. Student workflow

1. Select a date and group size under Find a room.
2. Choose an available one-hour start time. Hours are shown in Singapore time.
3. Add participants if needed; the organiser is included automatically. Admin accounts should be excluded after the participant fix is deployed.
4. Confirm the booking and check My bookings.
5. Reload to verify that the booking persists. A listed participant should also see it when signing in with their account.
6. The organiser can cancel a future booking. Confirm that the slot becomes available again.

Booking rules include room capacity, overlapping room/participant checks and at most two upcoming bookings organised by the same user. The AWS backend validates these rules.

## 5. Check-in and no-show

For a 16:00–17:00 booking, Check in is available from 16:00 through 16:15 Singapore time. Open My bookings and refresh if the button has not appeared. The organiser or any listed participant can check in. One check-in marks the entire group as attended and saves the check-in time to DynamoDB.

After the 15-minute window, a booking without check-in displays No-show when reloaded. Currently this is calculated for display: the stored attendance_outcome remains pending. No-show does not automatically cancel the booking or release its slot. This check-in does not verify physical presence.

## 6. Admin workflow

Sign in with the provisioned admin account and open Admin. Use Rooms to add or edit room name, capacity, location and active status. After a successful save, reload and confirm the change. Successful operations update the shared AWS Rooms table; a failed request is not proof of a successful save.

Use inactive status for rooms that should stop accepting new bookings. Coordinate changes with teammates. Room ID generation depends on the deployed backend version; verify the automatic ID update before claiming sequential IDs are implemented.

Reservation analytics and Demand patterns describe the historical analytics dataset, not necessarily bookings just created in the live DynamoDB table. Demand patterns are historical counts, not a prediction.

## 7. Troubleshooting

| Symptom | What to check |
| --- | --- |
| Page cannot be opened | Start the local server and leave its terminal running. |
| Port already in use | Use the existing server or stop it before starting another; keep port 8766. |
| Old interface remains | Pull the latest files, then hard-refresh with Command+Shift+R on Mac or Ctrl+Shift+R on Windows. |
| Sign-in redirect fails | Use exactly http://127.0.0.1:8766/ and ask the owner to check the Cognito callback URL. |
| 401 | Sign out and sign in again; the owner should check token/authorizer configuration if it persists. |
| 403 identity not mapped | The owner must map the Cognito issuer and subject to one active RoomlyUsers record. |
| 404 API request | The owner should check that the API route and Lambda integration are deployed. |
| 500 API request | The owner should inspect API Gateway access logs and Lambda logs; include the request path and time. |
| Failed to fetch | Check connectivity, API availability and CORS; use the browser Network panel to identify the failing request. |

Share error text, request path and time with the owner. Do not share passwords or Authorization headers/tokens in screenshots.

## 8. Before recording project evidence

Test login, booking persistence, participant visibility, conflicting bookings, cancellation, check-in and admin access restrictions. Record expected and actual results with a date. Redact sensitive fields. Local syntax checks and a successful Git push do not establish that every deployed AWS workflow passes.
