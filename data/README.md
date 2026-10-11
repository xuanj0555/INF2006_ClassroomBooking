# Roomly Data Documentation

## Purpose

Roomly uses two separate categories of data:

1. Historical university-library reservation data used for reservation-demand analytics.
2. Live application data used by the Roomly booking system.

The historical dataset is not inserted into the application's live booking tables. Historical reservation records also do not prove that a room was occupied because the source does not contain attendance or check-in information.

## Historical Dataset Source

- Dataset: **50,000+ University Library Room Reservations**
- Platform: Kaggle
- Source URL: https://www.kaggle.com/datasets/aceeedev/university-library-room-reservations
- Source period: 6 January 2024 to 31 December 2024
- Source page last updated: 6 January 2025
- Licence listed on Kaggle: MIT
- Expected source update frequency: Never

The MIT licence permits reuse and modification, subject to its licence conditions. Roomly uses the dataset for educational reservation-demand analysis.

The exact date on which the team originally downloaded the dataset was not recorded. The repository copy is therefore identified by its filename, row count and Git history rather than by a recorded download timestamp.

## Historical Dataset Files

### `reservations.csv`

Raw historical dataset downloaded from Kaggle.

- Rows: 51,826
- Distinct room identifiers: 46
- Date range: 6 January 2024 to 31 December 2024
- Used as the input to `prepare_reservations.py`
- Must not be manually edited

Original fields:

- `start_date`
- `end_date`
- `friendly_date`
- `duration`
- `room_number`

### `reservations_cleaned_newversion.csv`

Cleaned historical dataset used by:

- `analytics/reservation_analysis.ipynb`
- Dashboard analytics exports
- Analytics validation tests

The file is generated from `reservations.csv` by running:

```powershell
.\.venv\Scripts\python.exe data\prepare_reservations.py
```

Cleaned rows: 51,319.

Cleaned fields:

- `start_time`
- `end_time`
- `duration_minutes`
- `room_id`
- `reservation_date`
- `weekday`
- `start_hour`
- `month`
- `is_weekend`

Room identifiers are treated as text so that leading zeros, such as `033`, are preserved.

### `room_capacity.csv`

Contains the room-capacity reference used by the Roomly application and dashboard.

It is separate from the Kaggle reservation records. Historical room identifiers must not automatically be interpreted as actual rooms on the team's campus. Any capacity values that are not obtained from a documented institutional source must be described as project or demonstration values.

## Raw-to-Cleaned Processing

The reproducible cleaning script is:

```text
data/prepare_reservations.py
```

The script performs the following steps:

1. Loads `reservations.csv`.
2. Loads room identifiers as text to preserve leading zeros.
3. Parses the start and end timestamps.
4. Checks for missing or invalid timestamps.
5. Checks for missing room identifiers.
6. Checks for exact duplicate source rows.
7. Calculates reservation duration from the start and end timestamps.
8. Excludes records with an actual duration below 5 minutes.
9. Excludes records with an actual duration above 240 minutes.
10. Rounds valid timestamp-derived durations to the nearest whole minute.
11. Derives the reservation date, weekday, start hour, month and weekend indicator.
12. Writes `reservations_cleaned_newversion.csv`.

### Exclusion Counts

| Cleaning rule | Rows excluded |
|---|---:|
| Invalid timestamps | 0 |
| Missing room identifiers | 0 |
| Exact duplicate rows | 0 |
| Actual duration below 5 minutes | 1 |
| Actual duration above 240 minutes | 506 |
| **Total excluded** | **507** |

Final calculation:

```text
51,826 raw rows - 507 excluded rows = 51,319 cleaned rows
```

The single record below five minutes had a timestamp-derived duration of three minutes. The raw `duration` field stated five minutes, so the timestamps were treated as the authoritative duration source.

## Live Application and Sample Files

The following files are not inputs to the historical analytics notebook:

### `INF2006 - Booking.csv`

An early booking-table schema or placeholder for the live Roomly application. It currently contains no booking records.

### `INF2006 - Room.csv`

An early room-table schema or placeholder for the live Roomly application. It currently contains no room records.

### `INF2006 - User.csv`

An early user-table schema or placeholder for the live Roomly application. It currently contains no user records.

### `attendance.csv`

Contains three sample attendance records associated with example booking IDs. It is used for application development or demonstration and is not joined to the Kaggle historical dataset.

The historical dataset does not contain booking IDs that reliably link to this sample attendance file.

## Known Limitations

- The source timezone is not documented. The project does not convert the historical timestamps to Asia/Singapore.
- The historical records describe reservations, not confirmed attendance or physical occupancy.
- The dataset contains no user identities, participant lists, booking-creation timestamps, cancellation status or unsuccessful booking attempts.
- Nine dates within the covered period have no reservation starts. These may represent zero demand, closure dates or missing data.
- Two records overlap earlier reservations for the same room and require cautious interpretation.
- Overlapping reservations may inflate reserved-hour totals.
- Room identifiers in the historical dataset do not necessarily represent rooms available in the live Roomly application.
- Results describe the supplied 2024 historical dataset and should not automatically be treated as current demand.
- No forecasting or no-show prediction model is included in the current analytics deliverable.