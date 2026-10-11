# Roomly Reservation Analytics

This folder contains reproducible descriptive analytics for Roomly's historical reservation dataset.

The historical Kaggle dataset is used only for reservation-demand analytics. It is separate from the application's live bookings, users and attendance records.

## Files

- `reservation_analysis.ipynb` loads, validates and analyses the cleaned dataset.
- `reproduce.py` regenerates the cleaned dataset, executes the notebook and verifies that all expected outputs exist.
- `requirements.txt` contains the required Python dependencies.
- `output/reservations_by_room.csv` contains reservation count and reserved hours for each room.
- `output/reservations_by_weekday.csv` contains reservation count for each weekday.
- `output/reservations_by_start_hour.csv` contains reservation count for each start hour.
- `output/summary_metrics.json` contains overall dataset, duration and data-quality metrics.

## Input Data

The raw historical dataset is:

```text
data/reservations.csv
```

The reproducible cleaning script is:

```text
data/prepare_reservations.py
```

The cleaning script generates:

```text
data/reservations_cleaned_newversion.csv
```

The analytics notebook reads the generated cleaned file. Dataset provenance, cleaning rules, exclusions and known limitations are documented in:

```text
data/README.md
data/DATA_DICTIONARY.md
```

## Requirements

- Python 3.12
- pandas 3.0.6
- matplotlib 3.11.2
- nbconvert 7.17.1
- ipykernel 7.4.0

## Reproduction Instructions

Run all commands from the repository root.

### Windows PowerShell

Create and activate a virtual environment:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r analytics\requirements.txt
```

Run the complete analytics workflow with one command:

```powershell
python analytics\reproduce.py
```

### macOS or Linux

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r analytics/requirements.txt
```

Run the complete analytics workflow with one command:

```bash
python analytics/reproduce.py
```

The reproduction command:

1. Runs `data/prepare_reservations.py`.
2. Regenerates `data/reservations_cleaned_newversion.csv`.
3. Executes `analytics/reservation_analysis.ipynb`.
4. Writes the dashboard files consistently to `analytics/output/`.
5. Checks that all expected CSV and JSON outputs exist.

A successful run ends with:

```text
PASS: analytics reproduced successfully
Output location: <repository>/analytics/output
```

## Verified Dataset Totals

- Raw records: 51,826
- Excluded records: 507
- Cleaned records: 51,319
- Distinct room identifiers: 46
- Historical start-date range: 6 January 2024 to 31 December 2024

The 507 exclusions consist of:

- One reservation with a timestamp-derived duration below 5 minutes.
- 506 reservations with timestamp-derived durations above 240 minutes.

## Output Fields

### `reservations_by_room.csv`

| Field | Description |
|---|---|
| `room_id` | Historical room identifier stored as text |
| `reservation_count` | Number of reservations starting in that room |
| `reserved_hours` | Sum of reservation durations divided by 60 |

### `reservations_by_weekday.csv`

| Field | Description |
|---|---|
| `weekday` | Day of the week |
| `reservation_count` | Number of reservations starting on that weekday |

### `reservations_by_start_hour.csv`

| Field | Description |
|---|---|
| `start_hour` | Reservation starting hour from 0 to 23 |
| `reservation_count` | Number of reservations starting during that hour |

### `summary_metrics.json`

The summary includes:

- Record count
- Room count
- Average reservation duration
- Median reservation duration
- Total reserved hours
- Historical coverage start and end
- Number of detected overlapping cases
- Number of dates without reservation starts
- Source timezone status

## Verified Results

- Average reservation duration: 95.43 minutes
- Median reservation duration: 90 minutes
- Total reserved hours: 81,622.72 hours
- Highest reservation count by room: Room 105 with 2,107 reservations
- Highest reserved hours by room: Room 104 with 3,284.50 hours
- Busiest weekday: Wednesday with 9,233 reservations
- Busiest starting hour: 14:00 with 4,755 reservations

## Interpretation

The historical results suggest that demand was concentrated around the middle of the week and during daytime study hours. Wednesday recorded the highest reservation count, while 14:00 was the busiest starting hour.

Rooms 104, 105 and 106 recorded particularly high reserved-hour totals. If similar demand patterns apply to Roomly's actual campus rooms, these periods and rooms may require closer availability monitoring. Lower-demand periods could also be considered for maintenance or administrative activities.

These findings describe recorded reservations only. They do not establish actual room occupancy, attendance or unmet demand.

## Known Limitations

- The source timezone is unknown, so no timezone conversion is applied.
- Reservations do not prove that users attended or occupied a room.
- The historical dataset does not contain user identities, booking-creation timestamps, cancellation outcomes or unsuccessful booking attempts.
- Nine dates within the source period have no reservation starts. The dataset does not establish whether these represent closures, zero demand or missing data.
- Two overlapping reservation cases were retained and documented. They may slightly inflate reserved-hour totals.
- Historical room identifiers do not necessarily correspond to actual Roomly campus rooms.
- Results describe the supplied 2024 dataset and should not automatically be treated as current demand.
- The current analytics deliverable does not include forecasting or no-show prediction.

## Validation Evidence

Analytics validation and manual checks are recorded in:

```text
evidence/test-data-ai.md
```

Cloud and dashboard comparisons must record the test date, selected room, weekday and hour, together with expected and actual values.