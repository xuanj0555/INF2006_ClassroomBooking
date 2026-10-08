# Cloud Analytics Integration Test

## Objective
Verify that the AWS analytics endpoint returns Member 4's
historical reservation analysis stored in S3.

## Test date
8 October 2026

## AWS configuration
- Region: us-east-1
- S3 bucket: roomly-analytics-2026-11
- Lambda function: roomly-get-analytics
- Environment variable name: ANALYTICS_BUCKET
- API Gateway: roomly-api
- Route: GET /analytics
- Endpoint:
  https://kw67yao8v7.execute-api.us-east-1.amazonaws.com/analytics

## S3 output object keys
- analytics/output/summary_metrics.json
- analytics/output/reservations_by_room.csv
- analytics/output/reservations_by_weekday.csv
- analytics/output/reservations_by_start_hour.csv

## Procedure
1. Opened the analytics endpoint in the browser.
2. Copied the returned JSON.
3. Compared its summary with Member 4's saved summary_metrics.json.
4. Checked that reservation counts grouped by room, weekday
   and start hour each total 51,319.

## Expected and actual results

| Check | Expected | Actual | Result |
|---|---:|---:|---|
| Reservation count | 51,319 | 51,319 | PASS |
| Historical room count | 46 | 46 | PASS |
| Average duration in minutes | 95.43 | 95.43 | PASS |
| Median duration in minutes | 90 | 90 | PASS |
| Total reserved hours | 81,622.72 | 81,622.72 | PASS |
| Total grouped by room | 51,319 | 51,319 | PASS |
| Total grouped by weekday | 51,319 | 51,319 | PASS |
| Total grouped by start hour | 51,319 | 51,319 | PASS |

## Website integration status
PASS — The existing Reservation analytics page requested:
https://kw67yao8v7.execute-api.us-east-1.amazonaws.com/analytics

Chrome Network showed HTTP 200 OK.

The website displayed:
- 51,319 reservations
- 81,622.72 reserved hours
- 95.43 average reservation minutes

These values matched the saved analytics output.

Test date: 8 October 2026
Screenshot: evidence/analytics-website-network.png

## Evidence
- Saved response: evidence/analytics-api-response.json
- Endpoint screenshot: [enter filename after saving it]
- Lambda log request ID: Not recorded
- HTTP status code: Not separately recorded
- Endpoint screenshot: evidence/analytics-api-response.png

## Issue encountered
GET /analytics initially had no integration attached.
The existing integration selector showed only roomly-get-rooms.

Resolution:
Created and attached an integration for roomly-get-analytics.
The endpoint subsequently returned the expected analytics JSON.

## Limitations
These are historical reservation statistics, separate from
live bookings. Reservations do not prove attendance.
This test does not verify cloud booking creation or website
integration.
