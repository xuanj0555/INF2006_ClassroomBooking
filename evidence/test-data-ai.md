# Data and Analytics Test Evidence

## Component

Roomly historical reservation demand analytics.

## Data Source

- Source: University Library Room Reservations dataset from Kaggle
- Source URL: https://www.kaggle.com/datasets/aceeedev/university-library-room-reservations
- Analysed file: `data/reservations_cleaned_newversion.csv`
- Data dictionary: `data/DATA_DICTIONARY.md`
- Analysis notebook: `analytics/reservation_analysis.ipynb`

The historical dataset is used only for demand analytics. It is separate from Roomly's live booking records.

## Dataset Validation

| Validation | Result |
|---|---:|
| Reservation records | 51,319 |
| Distinct room identifiers | 46 |
| Missing values | 0 |
| Duplicate rows | 0 |
| Earliest reservation start | 2024-01-06 |
| Latest reservation start | 2024-12-31 |
| Overlap cases | 2 |
| Dates without reservation starts | 9 |
| Source timezone | Not specified |

All assertions in the notebook passed.

## Verified Analytics

| Metric | Result |
|---|---:|
| Average reservation duration | 95.43 minutes |
| Median reservation duration | 90 minutes |
| Total reserved time | 81,622.72 hours |
| Highest-demand room by count | Room 105 — 2,107 reservations |
| Highest reserved hours | Room 104 — 3,284.5 hours |
| Highest-demand weekday | Wednesday — 9,233 reservations |
| Highest-demand start hour | 14:00 — 4,755 reservations |

Reservation counts grouped by room, weekday and start hour each sum to 51,319.

## Manual Reserved-Hours Validation

The first five reservation durations were manually summed:

- Total duration: 630 minutes
- Conversion: 630 / 60
- Expected result: 10.5 hours
- Notebook result: 10.5 hours
- Test result: PASS

## Data-Quality Findings

Two overlap cases were found for Room 234:

1. 29 May 2024: 14:00–15:00 overlaps with 14:15–15:15.
2. 5 June 2024: 14:00–15:00 overlaps with 14:15–15:15.

Each case overlaps by 45 minutes. The records were retained and documented rather than deleted.

Nine weekend dates within the covered interval contained no reservation starts. It cannot be confirmed whether these represent zero demand, closures or missing source data.

The timestamps contain no timezone information. They are therefore treated as timezone-naive source-local times, and no timezone conversion is performed.

## Dashboard Output Files

The notebook produces:

- `analytics/output/reservations_by_room.csv`
- `analytics/output/reservations_by_weekday.csv`
- `analytics/output/reservations_by_start_hour.csv`
- `analytics/output/summary_metrics.json`

The exported files were reloaded and validated successfully.

## Reproduction

1. Install Python and the required dependencies.
2. Open `analytics/reservation_analysis.ipynb`.
3. Select the project virtual environment as the notebook kernel.
4. Run every cell from top to bottom.
5. Confirm that all validation cells display `PASS`.
6. Check the generated files inside `analytics/output/`.

## AI and Forecasting Scope

No no-show prediction or forecasting model is included in the current analytics scope. The current deliverable provides verified descriptive reservation-demand metrics. Forecasting may be added later only with chronological evaluation and a baseline comparison.