# Roomly Reservation Analytics

This folder contains reproducible descriptive analytics for Roomly's historical reservation dataset.

The historical Kaggle dataset is used only for reservation-demand analytics. It is separate from the application's live booking data.

## Files

- `reservation_analysis.ipynb` — loads, validates and analyses the historical dataset.
- `requirements.txt` — records the Python dependencies required to reproduce the analysis.
- `output/reservations_by_room.csv` — reservation count and reserved hours for each room.
- `output/reservations_by_weekday.csv` — reservation count for each weekday.
- `output/reservations_by_start_hour.csv` — reservation count for each start hour.
- `output/summary_metrics.json` — overall dataset and duration metrics.

All paths in this document are relative to the repository root.

## Data Source

- Dataset: University Library Room Reservations
- Source: Kaggle
- URL: https://www.kaggle.com/datasets/aceeedev/university-library-room-reservations
- Analysed file: `data/reservations_cleaned_newversion.csv`
- Data dictionary: `data/DATA_DICTIONARY.md`

## Requirements

- Python 3.12
- pandas
- matplotlib
- Jupyter or the VS Code Jupyter extension

The exact installed package versions are recorded in `analytics/requirements.txt`.

## Reproduction Instructions

From the repository root, create a virtual environment:

```powershell
python -m venv .venv
```

Install the required dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r analytics\requirements.txt
```

Then:

1. Open `analytics/reservation_analysis.ipynb`.
2. Select `.venv` as the notebook kernel.
3. Run every cell from top to bottom.
4. Confirm that all validation sections display `PASS`.
5. Check the generated files under `analytics/output/`.

## Verified Results

- 51,319 reservation records
- 46 room identifiers
- No missing values
- No duplicate rows
- Average reservation duration: 95.43 minutes
- Median reservation duration: 90 minutes
- Total reserved time: 81,622.72 hours
- Highest-demand room by count: Room 105 with 2,107 reservations
- Highest reserved hours: Room 104 with 3,284.5 hours
- Highest-demand weekday: Wednesday with 9,233 reservations
- Highest-demand start hour: 14:00 with 4,755 reservations
- Two overlapping reservation cases
- Nine dates without reservation starts

## Dashboard Output Fields

### reservations_by_room.csv

| Field | Type | Description |
|---|---|---|
| `room_id` | Text | Historical room identifier |
| `reservation_count` | Integer | Number of reservations for the room |
| `reserved_hours` | Decimal | Total hours reserved for the room |

Room identifiers must be loaded as text.

### reservations_by_weekday.csv

| Field | Type | Description |
|---|---|---|
| `weekday` | Text | Day of the week |
| `reservation_count` | Integer | Number of reservations for the weekday |

The dashboard should retain Monday-to-Sunday ordering.

### reservations_by_start_hour.csv

| Field | Type | Description |
|---|---|---|
| `start_hour` | Integer | Reservation start hour from 0 to 23 |
| `reservation_count` | Integer | Number of reservations starting during the hour |

### summary_metrics.json

The JSON file contains:

- `record_count`
- `room_count`
- `average_duration_minutes`
- `median_duration_minutes`
- `total_reserved_hours`
- `coverage_start`
- `coverage_end`
- `overlap_cases`
- `dates_without_reservation_starts`
- `source_timezone`

## Suggested Dashboard Charts

| Chart | Source file | Fields |
|---|---|---|
| Reservations by room | `reservations_by_room.csv` | `room_id`, `reservation_count` |
| Reserved hours by room | `reservations_by_room.csv` | `room_id`, `reserved_hours` |
| Demand by weekday | `reservations_by_weekday.csv` | `weekday`, `reservation_count` |
| Demand by start hour | `reservations_by_start_hour.csv` | `start_hour`, `reservation_count` |
| Summary cards | `summary_metrics.json` | Overall metrics |

## Validation

The notebook verifies that:

- Counts grouped by room sum to 51,319.
- Counts grouped by weekday sum to 51,319.
- Counts grouped by start hour sum to 51,319.
- All 46 room identifiers are represented.
- The exported files can be loaded successfully.
- The first five reservations total 630 minutes, or 10.5 reserved hours.

Detailed validation evidence is recorded in:

`evidence/test-data-ai.md`

## Data-Quality Findings

Two overlap cases were identified for Room 234:

1. On 29 May 2024, 14:00–15:00 overlaps with 14:15–15:15.
2. On 5 June 2024, 14:00–15:00 overlaps with 14:15–15:15.

Each case overlaps by 45 minutes. The records were retained and documented rather than deleted.

Nine weekend dates within the covered interval contain no reservation starts. It cannot be confirmed whether these dates represent genuine zero demand, library closures or missing source data.

The source timezone is not specified, and the timestamps contain no timezone offsets. They are treated as timezone-naive source-local times without conversion.

## Limitations

- The dataset contains no user identities.
- It contains no participant lists or attendance outcomes.
- It contains no booking-creation timestamps.
- It contains no cancellation status.
- Reservation demand does not necessarily represent actual room usage.
- No no-show prediction model is included in the current scope.
- Forecasting is not included in the current first deliverable.

## Project Scope

The current analytics component provides verified descriptive reservation-demand metrics for the Roomly dashboard.

Forecasting may be added later only after the descriptive metrics are integrated, using chronological evaluation and a baseline comparison.