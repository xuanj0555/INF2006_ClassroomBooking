# Roomly Analytics Deployment

## AWS configuration
- Region: us-east-1
- S3 bucket: roomly-analytics-2026-11
- Block all public access: [On/Off, as checked]
- Lambda function: roomly-get-analytics
- Lambda execution role: LabRole
- Lambda environment variable: ANALYTICS_BUCKET
- ANALYTICS_BUCKET value: roomly-analytics-2026-11
- API Gateway name: roomly-api
- API Gateway ID: kw67yao8v7
- Route: GET /analytics
- Endpoint:
  https://kw67yao8v7.execute-api.us-east-1.amazonaws.com/analytics

## S3 analytics output objects
- analytics/output/summary_metrics.json
- analytics/output/reservations_by_room.csv
- analytics/output/reservations_by_weekday.csv
- analytics/output/reservations_by_start_hour.csv

## How it works
API Gateway sends GET /analytics requests to roomly-get-analytics.
The Lambda reads the four analytics output files from the private
S3 bucket and returns the historical summary and grouped results
as JSON.

## Verification
The endpoint returned the expected analytics results:
- 51,319 reservations
- 46 historical rooms
- 95.43 average reservation minutes
- 81,622.72 total reserved hours

Detailed evidence: test-analytics-cloud.md

## Website integration
PASS — The Reservation analytics page requested the AWS
GET /analytics endpoint and received HTTP 200.
Displayed metrics matched the analytics response.
Test date: 8 October 2026

## Scope
This document covers the historical analytics service.
It does not confirm completion of cloud booking, authentication
or frontend hosting.
