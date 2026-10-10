# Cloud Analytics Integration Test

## Objective

Verify that the AWS analytics endpoint returns Member 4’s historical reservation analysis stored in S3, and that the Roomly website can retrieve and display the analytics.

## Test dates

- Initial cloud and website integration: 8 October 2026
- Authenticated endpoint access verification: 10 October 2026

## AWS configuration

- Region: `us-east-1`
- S3 bucket: `roomly-analytics-2026-11`
- Lambda function: `roomly-get-analytics`
- Environment variable: `ANALYTICS_BUCKET`
- API Gateway: `roomly-api`
- Route: `GET /analytics`
- Endpoint: `https://kw67yao8v7.execute-api.us-east-1.amazonaws.com/analytics`

## S3 output object keys

- `analytics/output/summary_metrics.json`
- `analytics/output/reservations_by_room.csv`
- `analytics/output/reservations_by_weekday.csv`
- `analytics/output/reservations_by_start_hour.csv`

## 1. Cloud analytics data verification

### Test date

8 October 2026

### Procedure

1. Requested the analytics endpoint.
2. Saved the returned JSON.
3. Compared its summary with Member 4’s saved `summary_metrics.json`.
4. Checked that reservation counts grouped by room, weekday and start hour each totalled 51,319.

### Expected and actual results

| Check | Expected | Actual | Result |
|---|---:|---:|---|
| Reservation count | 51,319 | 51,319 | Pass |
| Historical room count | 46 | 46 | Pass |
| Average duration in minutes | 95.43 | 95.43 | Pass |
| Median duration in minutes | 90 | 90 | Pass |
| Total reserved hours | 81,622.72 | 81,622.72 | Pass |
| Total grouped by room | 51,319 | 51,319 | Pass |
| Total grouped by weekday | 51,319 | 51,319 | Pass |
| Total grouped by start hour | 51,319 | 51,319 | Pass |

### Evidence

- Saved response: [analytics.json](analytics.json)
- Reference summary: [summary_metrics.json](../analytics/output/summary_metrics.json)

The initial endpoint request’s HTTP status and Lambda request ID were not separately recorded.

## 2. Website integration verification

### Test date

8 October 2026

### Procedure

1. Opened the existing Reservation analytics page.
2. Inspected its analytics request in Chrome Developer Tools → Network.
3. Checked the HTTP status.
4. Compared the displayed metrics with the saved analytics output.

### Actual result

The website requested:

```text
https://kw67yao8v7.execute-api.us-east-1.amazonaws.com/analytics
```

Chrome Network showed HTTP 200 OK.

The website displayed:

- 51,319 reservations.
- 81,622.72 reserved hours.
- 95.43 average reservation minutes.

These values matched the saved analytics output.

Result: Pass.

### Evidence

[Website analytics request and display](analytics-website-network.png)

## 3. Authenticated endpoint access verification

### Test date

10 October 2026

### Procedure

1. Signed in as Test Admin.
2. Sent a direct request to `GET /analytics` using the account’s login token.
3. Recorded the HTTP status and inspected the JSON response.
4. Sent a separate request without an Authorization header.

### Expected and actual results

| Request | Expected | Actual | Result |
|---|---|---|---|
| Authenticated administrator | HTTP 200 with analytics data | HTTP 200 with historical analytics JSON | Pass |
| No authentication token | HTTP 401 | HTTP 401 with `Unauthorized` response | Pass |

The administrator response included the summary and the `by_room`, `by_weekday` and `by_start_hour` sections.

### Evidence

- [Authenticated administrator response](security-analytics-admin.png)
- [No-token rejection](security-analytics-no-token.png)
- Detailed security record: [test-security.md](test-security.md)

These screenshots were captured on 10 October and are separate from the initial 8 October integration evidence.

## Issue encountered

Initially, `GET /analytics` had no integration attached. The existing integration selector showed only `roomly-get-rooms`.

### Resolution

Created and attached an integration for `roomly-get-analytics`. The endpoint subsequently returned the expected analytics JSON.

## Conclusion

The recorded comparisons show that the cloud endpoint returned values matching the saved historical analytics outputs. The website integration test showed a successful request and matching displayed summary metrics.

The later access tests confirmed successful authenticated administrator access and rejection of a request without a token.

## Limitations

- The analytics describe historical reservations and are separate from live DynamoDB bookings.
- Reservations do not prove attendance or actual occupancy.
- Matching cloud outputs demonstrates consistency with the saved analysis; it does not independently establish the correctness of every calculation.
- This test does not verify cloud booking creation, cancellation or conflict prevention.
- Student access to the analytics endpoint has not been tested here, so administrator-only access is not established.
- Lambda request identifiers were not recorded for these analytics tests.
```
