# Roomly Deployment Record

## Scope

This document records Roomly’s AWS backend configuration, local frontend setup, deployment procedure and verification evidence.

The frontend runs locally. Authentication, booking storage, API processing and historical analytics delivery use AWS services.

## 1. Architecture overview

- Region: `us-east-1`
- Frontend: Locally served HTML, CSS and JavaScript
- Authentication: Amazon Cognito
- API: Amazon API Gateway HTTP API
- Compute: AWS Lambda
- Live application storage: Amazon DynamoDB
- Historical analytics storage: Amazon S3
- Monitoring: Amazon CloudWatch

[Architecture diagram](architecture.png)

## 2. Frontend setup

From the repository root, run:

### macOS

```text
python3 -m http.server 8766 --bind 127.0.0.1 --directory src/frontend
```

### Windows

```text
py -m http.server 8766 --bind 127.0.0.1 --directory src/frontend
```

Open:

```text
http://127.0.0.1:8766/
```

Keep the terminal running while using the website.

The frontend is not hosted in S3. Each teammate can run the frontend locally and connect to the same AWS backend using an authorised application account.

Application instructions: [USER_GUIDE.md](../USER_GUIDE.md).

## 3. Booking Lambda

### Configuration

| Setting | Value |
|---|---|
| Function | `roomly-booking-api` |
| Region | `us-east-1` |
| Actual ZIP upload date | 11 October 2026 |
| Runtime | Python 3.13 |
| Handler | `lambda_handler.lambda_handler` |
| Execution role | `LabRole` |
| Allocated memory | 256 MB |
| Timeout | 15 seconds |

### Deployment package

```text
roomly-booking-api.zip
├── lambda_handler.py
└── dynamodbService.py
```

Both files are placed at the ZIP root.

Repository sources:

- [lambda_handler.py](../src/backend/lambda_handler.py)
- [dynamodbService.py](../src/backend/dynamodbService.py)

### Environment variables

| Variable | Value |
|---|---|
| `ROOMS_TABLE` | `Rooms` |
| `USERS_TABLE` | `RoomlyUsers` |
| `BOOKINGS_TABLE` | `RoomlyBookings` |
| `RESERVATIONS_TABLE` | `RoomlyReservations` |
| `AUTH_ISSUER` | `https://cognito-idp.us-east-1.amazonaws.com/us-east-1_EtQjacsSX` |

Detailed settings: [Lambda configuration](../src/infrastructure/lambda_config.md).

### Deployment procedure

1. Package the matching handler and DynamoDB service files at the ZIP root.
2. Open AWS Lambda and select `roomly-booking-api`.
3. Select Code → Upload from → .zip file and upload the package.
4. Confirm the runtime, handler, environment variables, memory, timeout and execution role.
5. Wait for the function update to complete.
6. Confirm the relevant API Gateway routes integrate with this function.
7. Refresh Roomly and test the affected workflows.
8. Record the actual results and supporting evidence.

The deployed package must match the submitted repository source. Repeat affected tests after subsequent code changes.

## 4. Authentication

### Cognito configuration

| Setting | Value |
|---|---|
| User pool region | `us-east-1` |
| User pool ID | `us-east-1_EtQjacsSX` |
| App client | `roomly-web` |
| App client ID | `7bqthe08cf0fovnaqa43chjec5` |
| Client secret | None |
| OAuth grant | Authorization code |
| Frontend flow | Authorization code with PKCE |
| Scopes | `openid`, `email` |
| Callback URL | `http://127.0.0.1:8766/` |
| Sign-out URL | `http://127.0.0.1:8766/` |

### Identity and permissions

API Gateway validates tokens through the `roomly-cognito` JWT authorizer.

The booking backend maps the verified token’s issuer and subject to `auth_issuer` and `auth_sub` in `RoomlyUsers`.

Backend checks enforce administrator permissions and booking-cancellation ownership.

Detailed configuration: [Cognito configuration](../src/infrastructure/cognito-config.md).

## 5. API Gateway

- Name: `roomly-api`
- ID: `kw67yao8v7`
- Type: HTTP API
- Region: `us-east-1`
- Stage: `$default`
- Automatic deployment: Enabled
- JWT authorizer: `roomly-cognito`

### Integrations

| Routes | Lambda integration |
|---|---|
| Session, users, availability, bookings, check-in and administrator operations | `roomly-booking-api` |
| `GET /rooms` | `roomly-get-rooms` |
| `GET /analytics` | `roomly-get-analytics` |

Complete routes, JWT settings and CORS settings: [API Gateway configuration](../src/infrastructure/api-gateway-config.md).

## 6. DynamoDB

Roomly stores live application data in:

| Table | Purpose |
|---|---|
| `Rooms` | Room details, capacity, location and active status |
| `RoomlyUsers` | Application users, identity mapping and permissions |
| `RoomlyBookings` | Booking details, participants, status and attendance |
| `RoomlyReservations` | Room/user slot locks and system records |

The booking service uses conditional transactions to maintain booking records and reservation locks together. Cancellation retains the booking history while releasing the applicable locks.

Table keys, attributes and transaction behaviour: [DynamoDB schema](../src/infrastructure/dynamodb-schema.md).

## 7. Historical analytics deployment

### AWS configuration

- Region: `us-east-1`
- S3 bucket: `roomly-analytics-2026-11`
- Block all public access: On
- Lambda function: `roomly-get-analytics`
- Lambda execution role: `LabRole`
- Environment variable: `ANALYTICS_BUCKET`
- Environment variable value: `roomly-analytics-2026-11`
- API Gateway: `roomly-api`
- Route: `GET /analytics`
- Endpoint: `https://kw67yao8v7.execute-api.us-east-1.amazonaws.com/analytics`

Repository source: [analytics_lambda.py](../src/backend/analytics_lambda.py).

### S3 output objects

- `analytics/output/summary_metrics.json`
- `analytics/output/reservations_by_room.csv`
- `analytics/output/reservations_by_weekday.csv`
- `analytics/output/reservations_by_start_hour.csv`

### Data flow

API Gateway sends `GET /analytics` requests to `roomly-get-analytics`.

The Lambda reads the four historical analytics files from the private S3 bucket and returns the summary and grouped results as JSON.

Historical analytics are separate from live DynamoDB bookings.

### Verification

The recorded endpoint response matched these saved analytics values:

- 51,319 reservations.
- 46 historical rooms.
- 95.43 average reservation minutes.
- 81,622.72 total reserved hours.

On 8 October 2026, the Reservation analytics page requested the endpoint and received HTTP 200. Displayed summary metrics matched the saved analytics output.

On 10 October 2026, a direct authenticated administrator request returned HTTP 200, and a request without a token returned HTTP 401.

Detailed evidence: [Cloud analytics integration test](test-analytics-cloud.md).

Storage settings: [S3 configuration](../src/infrastructure/s3-config.md).

## 8. Booking update and administrator room-creation verification

### Issue

The frontend expected the backend to assign room IDs automatically. The earlier deployed backend rejected creation without a supplied room ID with HTTP 400 and `Invalid room ID`.

### Resolution package

The replacement package contains the repository implementation of automatic room-ID generation and its matching Lambda handler.

The prepared source passed 70 automated tests on 11 October 2026, including mock DynamoDB room-ID generation and concurrent room-creation tests. These automated tests do not establish successful AWS deployment.

### Deployed verification record

- Test date: 11 October 2026
- Account: Test Admin
- Room name: Study Room E
- Capacity: 5
- Location: Random Wing
- Active: Yes

Steps:

1. Upload the replacement booking ZIP and wait for the update to complete.
2. Sign in as Test Admin.
3. Create the room without entering a room ID.
4. Record its assigned ID.
5. Refresh and confirm that the room remains visible.

Expected result: The backend assigns a unique room ID and the saved room persists after refreshing.

Actual results:

- Room creation: Succeeded
- Assigned room ID: R006
- Visible after refreshing: Yes
- Result: Pass

Evidence: [Administrator room creation](admin-room-created.png).

Mark this test Pass only after both creation and persistence are verified.

## 9. Supporting verification

| Area | Record |
|---|---|
| Booking workflow, persistence and cancellation | [Functional test](test-functional.md) |
| Authentication and permission checks | [Security tests](test-security.md) |
| Backend rules and mock DynamoDB transactions | [Backend tests](test-backend.md) |
| Analytics calculations and validation | [Data analytics test](test-data-ai.md) |
| Analytics API and website integration | [Cloud analytics test](test-analytics-cloud.md) |
| Retrieval of an earlier S3 object version | [Recovery test](test-resilience.md) |
| Current API logs and Lambda execution metrics | [Monitoring tests](monitoring.md) |
| Threats and controls | [Threat-control map](threat-control-map.md) |

Each test record states its own date and scope. Earlier test results should not be treated as proof of every later deployment.

## 10. Limitations and secret handling

- The frontend is locally served, rather than cloud hosted.
- Live use requires an available AWS backend, internet connectivity and a valid application account.
- The prototype uses AWS Academy LabRole. Restricted IAM inspection prevents complete verification of its permission scope.
- Mock DynamoDB tests do not replace deployed conflict tests. Their completion status is recorded in the backend test document.
- The analytics access tests demonstrate no-token rejection and administrator success; they do not establish administrator-only access.
- S3 version retrieval demonstrates object recoverability, not recovery of DynamoDB or the whole application.
- Historical analytics do not provide no-show prediction or prove actual occupancy.
- Passwords, tokens and AWS credentials must be excluded from the submission. Screenshots must be redacted as required by the project brief.

Execution-role details: [IAM access record](../src/infrastructure/iam-access.md).
