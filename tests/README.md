# Roomly — Campus Room Booking and Reservation-Demand Analytics

## 1. Project Overview

Roomly helps students and faculty find and reserve campus rooms
for individual study and group activities. It supports room
availability checks, group bookings and cancellations, with
rules that prevent conflicting room and participant reservations.

We created Roomly to make room booking easier and help
administrators understand how rooms are reserved. By analysing
historical reservation data, Roomly highlights popular rooms,
peak booking periods and reserved hours to support room
availability and scheduling decisions.

## 2. Team Members

| Name | Student ID
|------|------------
| Wei YuChen | 2503041@sit.singaporetech.edu.sg
| Stanberley Su | 2501376@sit.singaporetech.edu.sg 
| Sharlene Teo | 2503489@sit.singaporetech.edu.sg
| Shermaine Chan | 2501469@sit.singaporetech.edu.sg
Detailed contributions are recorded in
[TEAM_CONTRIBUTIONS.md](TEAM_CONTRIBUTIONS.md).

## 3. Intended Features

### Students and Faculty

- View rooms and available time slots.
- Create a room booking.
- Include registered users as participants.
- View and cancel their own future bookings.
- Receive clear messages when booking rules are not satisfied.

### Authorised Administrators

- Manage room availability and authorised booking operations.
- View reservation counts and reserved hours.
- Compare reservation patterns by room, date, hour and weekday.

Faculty membership does not automatically grant administrator permissions.

## 4. Booking Rules

- Only authenticated, active users may create bookings.
- Bookings use one-hour slots between 09:00 and 18:00,
  displayed in Asia/Singapore time.
- The final slot is 17:00–18:00.
- Bookings must be for a future time.
- Each room may have only one confirmed booking per slot.
- The organiser is automatically included as a participant.
- Participants must be registered, active users.
- Duplicate participants are not permitted.
- Total participants cannot exceed room capacity.
- A participant cannot belong to two confirmed bookings
  during the same slot.
- A user may organise at most two future confirmed bookings.
- Cancellation releases the room and participant reservations.
- The room booking and participant reservations must be saved
  together. If any part fails, none of the changes are saved.

Full rules are documented in
[src/booking_rules.md](src/booking_rules.md).

These are the intended rules. Some still require implementation.

## 5. Architecture

[View the architecture diagram](evidence/architecture.png)

The architecture diagram must reflect the current project scope
and be updated as implementation progresses.

### Proposed Booking Flow

Browser → API Gateway → Booking Lambda → DynamoDB

Cognito provides user authentication.
Amplify Hosting serves the website.

### Proposed Analytics Flow

Historical dataset → Python analytics → Results stored in S3

Browser → API Gateway → Analytics Lambda → Results in S3

CloudWatch provides operational logs and monitoring.

### Proposed AWS Components

| Service | Purpose |
|---------|---------|
| Amplify Hosting | Host the frontend |
| Amazon Cognito | Authenticate users |
| API Gateway | Receive authenticated API requests |
| AWS Lambda | Process booking rules and return analytics |
| Amazon DynamoDB | Store live application records |
| Amazon S3 | Store historical datasets and analytics results |
| Amazon CloudWatch | Collect logs and operational metrics |

The local Python server and SQLite database must be adapted
before deployment to Lambda and DynamoDB.

## 6. Technologies

### Current Local Prototype

- HTML
- CSS
- JavaScript
- Python standard library
- SQLite

### Planned Analytics

- Python scripts or notebooks
- Dependencies documented in analytics/requirements.txt
  when implemented

### Planned Cloud Platform

- Amazon Web Services (AWS)

## 7. Repository Structure

- README.md — project overview and setup instructions
- project_manifest.yaml — project summary and evidence paths
- src/frontend/ — website files
- src/backend/ — backend application code
- src/.env.example — placeholder configuration
- src/booking_rules.md — application rules
- data/reservations_cleaned.csv — cleaned historical data
- data/DATA_DICTIONARY.md — fields, types and definitions
- data/README.md — dataset source and processing notes
- analytics/ — analytics code and reproduction instructions
- tests/ — repeatable tests
- evidence/ — diagrams, test results and monitoring evidence
- TEAM_CONTRIBUTIONS.md — individual contributions
- AI_USE_DECLARATION.md — AI assistance and attribution

The final submission will also include report.pdf.
An optional presentation link may be placed in video_link.txt.

## 8. Run the Website Locally

### Prerequisites

- Python 3.9 or later
- A modern web browser
- A downloaded and extracted copy, or clone, of this repository

The supplied website prototype does not require additional
Python packages.

Run the following commands from the repository root:
the folder containing src, data and README.md.

### macOS

1. Open Terminal in the project folder.
2. Run: `python3 src/backend/server.py`
3. Open http://127.0.0.1:8765 in a browser.

### Windows

1. Extract the repository ZIP.
2. Open the project folder in File Explorer.
3. Type `cmd` in the address bar and press Enter.
4. Run: `py src\backend\server.py`
5. If necessary, try: `python src\backend\server.py`
6. Open http://127.0.0.1:8765 in a browser.

### Using the Prototype

- Choose a fictional demo account.
- Select a room and future time slot.
- Confirm the booking.
- View or cancel the booking from My bookings.

Keep the terminal open while using the website.
Press Ctrl+C to stop the server.

The Python server serves both the frontend and backend.
Do not open index.html directly.

### Local Storage

The prototype creates bookings.sqlite3 in the project root.

Bookings persist after the server restarts.
Demo sessions do not persist after a restart.

Each teammate's local copy has a separate database.
GitHub shares source code, not live booking records.

### Troubleshooting

- Address already in use:
  Check whether Roomly is already running on port 8765.
  Stop a known previous instance before restarting.

- Cannot find server.py:
  Confirm that the ZIP is extracted and the terminal is
  in the repository root.

- Python command not found:
  Install Python and reopen the terminal.

- Website unavailable:
  Check that the server is running and inspect its terminal output.

## 9. Application Data Model

Roomly uses four proposed logical tables.

| Table | Purpose |
|-------|---------|
| Users | Account identity, school ID, role and access status |
| Rooms | Room details, capacity and availability |
| Bookings | Organiser, room, reserved times and booking status |
| BookingParticipants | Users included in each booking |

Fields, types and relationships are documented in
[data/DATA_DICTIONARY.md](data/DATA_DICTIONARY.md).

The physical DynamoDB design must support the required queries
and atomic room/participant conflict prevention.

## 10. Historical Reservation Dataset

### Source

[University Library Room Reservations — Kaggle](https://www.kaggle.com/datasets/aceeedev/university-library-room-reservations)

### Cleaned File

`data/reservations_cleaned.csv`

### Reviewed Dataset Summary

- 51,319 reservation records
- 46 distinct room identifiers
- Reservation start dates from 6 January to 31 December 2024

This historical dataset is separate from live application records.

Dataset source, licence, download/version information and cleaning
steps must be documented in data/README.md.

### Data Considerations

- Keep room identifiers as text to preserve leading zeros and letters.
- booking_date currently represents the reservation start date,
  not the date the booking was created.
- The source timezone is not yet confirmed.
- Historical durations range from 5 to 240 minutes.
- Preserve historical durations rather than applying the
  application's one-hour rule to them.
- Some durations differ from timestamp calculations by up to
  30 seconds, consistent with rounding.
- Two records overlap earlier reservations for the same room
  identifier and require review.
- Nine dates within the covered interval have no reservation starts.
  Their meaning must be considered before filling daily counts
  with zero.

## 11. Reservation-Demand Analytics

Planned dashboard metrics include:

- Reservation counts by room and period
- Peak reservation hours and weekdays
- Total reserved hours
- Average reservation duration

The analytics describe recorded reservations.
They do not establish physical occupancy or unsuccessful
booking attempts.

Overlapping records must be reviewed before interpreting
summed durations as reserved room time.

Analytics code, dependencies and reproduction instructions
will be maintained in analytics/.

Demand forecasting may be added as an extension.
If implemented, it will use chronological evaluation and
comparison with a simple baseline.

## 12. Testing and Evidence

### Run the Supplied Backend Tests

macOS:

`python3 tests/test_backend.py`

Windows:

`py tests\test_backend.py`

The supplied tests need to remain aligned with the current
implementation and project scope.

Passing local tests does not demonstrate cloud deployment
or features that have not yet been implemented.

### Planned Evidence

| Area | Example check |
|------|---------------|
| Functional | A valid booking succeeds and a conflicting booking is rejected |
| Security | An unauthorised cancellation is rejected |
| Data/analytics | Metrics match manually calculated sample results |
| Scalability/resilience | A selected scaling or recovery mechanism is tested |
| Operations | A controlled event can be located in monitoring output |

Each test record should include:

- Objective
- Setup
- Commands or steps
- Expected result
- Actual result
- Test date
- Supporting artefact path

Store evidence in evidence/ and reference it in
project_manifest.yaml.

## 13. Security and Configuration

- Keep the demo server local until appropriate production
  controls are implemented.
- Do not commit passwords, access keys, tokens or personal data.
- Use fictional accounts for development and submitted samples.
- Store placeholder configuration only in .env.example.
- Exclude local .env files, *.sqlite3 files and __pycache__/
  from Git.
- Enforce permissions and booking rules in the backend.
- Configure least-privilege access for cloud components.

## 14. Attribution and AI Use

AI-assisted work, external code, dataset sources, licences
and verification activities are documented in
[AI_USE_DECLARATION.md](AI_USE_DECLARATION.md).
