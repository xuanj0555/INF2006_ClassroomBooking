# Evidence index

This folder contains test records, screenshots, logs and configuration evidence for Roomly. Read the written records for procedures, expected results, actual results, dates and limitations.

## Test records

| Record | Coverage |
|---|---|
| [Functional tests](test-functional.md) | Booking persistence, participant visibility and cancellation |
| [Backend tests](test-backend.md) | Automated tests and deployed booking conflict checks |
| [Security tests](test-security.md) | Authentication, administrator permissions and cancellation authorisation |
| [Interface tests](test-ui.md) | Role-based screens, booking forms, layout and simulated error handling |
| [Authentication interface tests](test-auth-ui.md) | Sign-in and authentication behaviour |
| [Data and analytics validation](test-data-ai.md) | Dataset cleaning, calculations and reproduction |
| [Cloud analytics integration](test-analytics-cloud.md) | Analytics API access and dashboard values |
| [Resilience test](test-resilience.md) | Retrieval of earlier S3 object versions |
| [Monitoring](monitoring.md) | CloudWatch logs and operational queries |

## Architecture and deployment

- [Architecture diagram](architecture.png)
- [Deployment record](deployment.md)
- [Threat-control mapping](threat-control-map.md)

## Supporting evidence

Screenshots, logs and exported results are linked from the relevant records and listed in the root project_manifest.yaml.

Screenshots support the written test records; they do not establish broader functionality beyond the recorded test.

## Scope and limitations

- Automated local and mocked DynamoDB tests are separate from deployed AWS tests.
- Simultaneous identical requests do not establish competition between different eligible organisers.
- Local login-expiry simulation does not test the server HTTP 401 handling path.
- Analytics request blocking simulates a network failure.
- S3 version retrieval does not demonstrate restoration as the current object or whole-application recovery.
- High-load performance has not been established.
