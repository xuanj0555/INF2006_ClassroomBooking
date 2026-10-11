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

## Raw-to-Clean Processing Validation

Test date: 11 October 2026

The cleaning process was reproduced using `data/prepare_reservations.py`.

| Check | Expected | Actual | Result |
|---|---:|---:|---|
| Raw records | 51,826 | 51,826 | PASS |
| Invalid timestamps excluded | 0 | 0 | PASS |
| Missing room identifiers excluded | 0 | 0 | PASS |
| Exact duplicate rows excluded | 0 | 0 | PASS |
| Durations below 5 minutes excluded | 1 | 1 | PASS |
| Durations above 240 minutes excluded | 506 | 506 | PASS |
| Total records excluded | 507 | 507 | PASS |
| Final cleaned records | 51,319 | 51,319 | PASS |

The cleaning script derives each reservation duration from `end_time - start_time`, rounds it to the nearest whole minute and exports the cleaned data to `data/reservations_cleaned_newversion.csv`.

## Independent Metric Validation

Test date: 11 October 2026

The following values were calculated independently by filtering the cleaned CSV outside the analysis notebook:

| Check | Expected | Actual | Result |
|---|---:|---:|---|
| Reservations for Room 105 | 2,107 | 2,107 | PASS |
| Reservations starting on Wednesday | 9,233 | 9,233 | PASS |
| Reservations starting at hour 14 | 4,755 | 4,755 | PASS |

The saved AWS response in `evidence/analytics.json` was independently checked on 11 October 2026.

| Metric | Cleaned CSV | Saved cloud response | Displayed dashboard | Status |
|---|---:|---:|---:|---|
| Room 105 reservation count | 2,107 | 2,107 | Not visible in saved evidence | CSV/cloud PASS; display pending |
| Wednesday reservation count | 9,233 | 9,233 | Not visible in saved evidence | CSV/cloud PASS; display pending |
| Start hour 14 reservation count | 4,755 | 4,755 | Not visible in saved evidence | CSV/cloud PASS; display pending |

The existing dashboard screenshot verifies HTTP 200 and the overall summary metrics. It does not display these three detailed values. During a retest on 11 October 2026, `GET /session` returned HTTP 500, preventing the administrator analytics navigation from loading. Detailed dashboard verification therefore remains pending for Members 1 and 3 after the session endpoint is restored.

## Reproduction Test

Test date: 11 October 2026

A separate temporary Python virtual environment was created to test the workflow independently from the normal project environment. The dependencies in `analytics/requirements.txt` were installed successfully.

The complete workflow was then executed using:

```powershell
& "$env:TEMP\roomly-analytics-test-20261011\Scripts\python.exe" analytics\reproduce.py