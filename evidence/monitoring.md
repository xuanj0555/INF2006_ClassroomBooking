# Roomly Monitoring Test

## Objective
Verify that CloudWatch records execution duration and memory usage
for the room-list Lambda.

## Test Date
24 September 2026

## Setup
- Region: us-east-1
- Function: roomly-get-rooms
- Log group: /aws/lambda/roomly-get-rooms
- An existing invocation report is available.

## Steps
1. Open the CloudWatch log group.
2. Open the log stream containing the invocation.
3. Enter REPORT in the Filter events box and press Enter.
4. Expand the matching report.

## Expected Result
A REPORT entry displays execution duration and memory usage.

## Actual Result
One matching REPORT entry appeared.

- Invocation timestamp: 2026-09-24T14:00:34.435Z
- Execution duration: 36.53 ms
- Billed duration: 37 ms
- Allocated memory: 128 MB
- Maximum memory used: 92 MB

## Interpretation
The filter successfully retrieved an execution report.
Reported memory usage was below the allocated memory.

This single invocation does not demonstrate performance under load
or prove that the API returned the correct room data.

## Supporting Evidence
[Lambda execution log](lambda-report-2026-09-24.txt)
