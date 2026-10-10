# Roomly Monitoring Tests

## Objective

Verify that CloudWatch records Lambda execution information and current API Gateway requests, and supports searching for HTTP 500 errors.

## 1. Lambda execution report

### Test date

24 September 2026

### Setup

- Region: `us-east-1`
- Function: `roomly-get-rooms`
- Log group: `/aws/lambda/roomly-get-rooms`
- An existing invocation report is available.

### Steps

1. Open the CloudWatch log group.
2. Open the log stream containing the invocation.
3. Enter `REPORT` in the Filter events box and press Enter.
4. Expand the matching report.

### Expected result

A REPORT entry displays execution duration, billed duration, allocated memory and maximum memory used.

### Actual result

One matching REPORT entry appeared.

| Metric | Observed value |
|---|---|
| Invocation timestamp | `2026-09-24T14:00:34.435Z` |
| Execution duration | 36.53 ms |
| Billed duration | 37 ms |
| Allocated memory | 128 MB |
| Maximum memory used | 92 MB |

Result: Pass.

### Interpretation

The filter successfully retrieved a Lambda execution report. Reported maximum memory usage was below the allocated memory.

This single invocation does not demonstrate performance under load or prove that the API returned the correct room data.

### Supporting evidence

[Lambda execution log](lambda-report-2026-09-24.txt)

## 2. Current API Gateway access logging

### Test date

10 October 2026

### Setup

- Region: `us-east-1`
- API: `roomly-api`
- Log group: `/aws/apigateway/roomly-api`
- Endpoint: `GET /session`
- Tool: CloudWatch log-event search
- Display timezone: UTC

### Steps

1. Perform an authenticated session request from Roomly.
2. Open the API Gateway log group in CloudWatch.
3. Select Search log group to view events across log streams.
4. Select the Last 1 hour time range.
5. Apply the following filter:

```text
{ $.route = "GET /session" }
```

6. Expand the recent session event.
7. Record its timestamp, request identifier, route, status and error fields.

### Expected result

A recent session request appears with its timestamp, request identifier, route and HTTP response status.

### Actual result

The expanded event contained:

| Field | Observed value |
|---|---|
| Timestamp | `2026-10-10T15:21:24.414Z` |
| Singapore time | 10 October 2026, 23:21:24.414 |
| Request ID | `FCKuRj-_oAMEaFw=` |
| Route | `GET /session` |
| HTTP status | `200` |
| Integration error | `-` |
| Error | `-` |

Result: Pass.

### Interpretation

CloudWatch recorded a recent successful session request. The event provides a timestamp and request identifier for investigation, together with the route and HTTP status. Neither displayed error field reported an error.

The API access-log event does not contain Lambda execution duration or memory usage; those metrics are demonstrated separately in Test 1.

### Supporting evidence

[Session access-log screenshot](monitoring-session-log.png)

## 3. HTTP 500 error search

### Test date

10 October 2026

### Setup

- Region: `us-east-1`
- Log group: `/aws/apigateway/roomly-api`
- Selected time range: Last 1 hour
- Screenshot capture time: Approximately 23:25 Singapore time

### Steps

1. Open the log group’s combined log-event view.
2. Select the Last 1 hour time range.
3. Apply the following filter:

```text
{ $.status = "500" }
```

4. Refresh the results.
5. Record whether any matching events appear.

### Expected result

The search displays logged events with HTTP status 500, or reports no matching events when none are found in the selected period.

### Actual result

CloudWatch displayed:

```text
No events found
```

Result: Pass for completing the monitoring search.

### Interpretation

No logged HTTP 500 events matched the filter during the selected one-hour period.

This result does not establish that the application has never experienced errors. The filter checks HTTP 500 specifically and does not cover other response statuses.

### Supporting evidence

[HTTP 500 search screenshot](monitoring-errors-query.png)

## Conclusion

The evidence demonstrates that CloudWatch records Lambda execution duration and memory usage, captures a current API Gateway session request, and supports filtering access logs for HTTP 500 responses.

The recorded session event returned HTTP 200. No HTTP 500 events were found in the selected one-hour monitoring period.

## Limitations

- The Lambda execution report and API access-log evidence were collected on different dates and represent separate requests.
- Individual requests do not establish performance, capacity or reliability under load.
- The HTTP 500 search covers only the selected time range and log group.
- These tests do not demonstrate automated alarms or notifications.
- Monitoring evidence supports investigation but does not replace functional, security or recovery testing.
