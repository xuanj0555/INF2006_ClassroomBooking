
# S3 Configuration

Recorded on: 10 October 2026

## Bucket

Bucket name: roomly-analytics-2026-11  
Region: us-east-1

Purpose: Stores historical reservation analytics outputs.
Live Roomly bookings are stored separately in DynamoDB.

## Access and protection

Block all public access: On

Bucket Versioning: Enabled

Default encryption: Server-side encryption with Amazon S3 managed keys (SSE-S3)

The analytics Lambda accesses the objects through its execution
role. The frontend requests analytics through API Gateway rather
than reading the bucket directly.

## Analytics objects

- analytics/output/summary_metrics.json
- analytics/output/reservations_by_room.csv
- analytics/output/reservations_by_weekday.csv
- analytics/output/reservations_by_start_hour.csv

## Application integration

Lambda function: roomly-get-analytics

Environment variable:
ANALYTICS_BUCKET = roomly-analytics-2026-11

API route: GET /analytics

The Lambda reads the four output files and returns the summary
and grouped historical reservation metrics as JSON.

## Version recovery

The version-retrieval test is documented in
evidence/test-resilience.md.

It demonstrates retrieval of an earlier test-object version
after an overwrite. It does not demonstrate recovery of the
whole application or DynamoDB data.

## Lifecycle rules

No lifecycle rules configured.
