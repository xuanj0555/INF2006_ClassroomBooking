# Roomly infrastructure setup

Roomly uses an AWS backend in us-east-1 with a locally served
frontend. The configuration records below describe the prototype.

## Setup order

1. Create the DynamoDB tables and application user records.
   See [DynamoDB schema](dynamodb-schema.md).

2. Configure the Cognito user pool and app client, including
   callback and sign-out URLs. Map Cognito identities to RoomlyUsers.
   See [Cognito configuration](cognito-config.md).

3. Create the private S3 analytics bucket and upload the four
   analytics output files.
   See [S3 configuration](s3-config.md).

4. Package and deploy the booking and analytics Lambda functions.
   Configure handlers, environment variables, execution roles,
   memory and timeout.
   See [Lambda configuration](lambda_config.md).

5. Configure API Gateway routes, Lambda integrations, JWT
   authorisation and CORS.
   See [API Gateway configuration](api-gateway-config.md).

6. Confirm logging and required resource access.
   See [IAM access](iam-access.md) and
   [monitoring evidence](../../evidence/monitoring.md).

7. Start the frontend and perform the documented verification.
   See [startup instructions](../../START_HERE.md) and
   [deployment record](../../evidence/deployment.md).

## Frontend configuration

The static frontend does not automatically load .env files.

Cognito settings are configured in src/frontend/auth.js.
The API base address is configured in the frontend JavaScript.

Keep the frontend configuration consistent with the deployed API,
Cognito client, callback URL and API Gateway CORS settings.

## Backend environment variables

The booking Lambda reads:

- AUTH_ISSUER
- ROOMS_TABLE
- USERS_TABLE
- BOOKINGS_TABLE
- RESERVATIONS_TABLE

The analytics Lambda reads:

- AUTH_ISSUER
- USERS_TABLE
- ANALYTICS_BUCKET

See ../.env.example for placeholder values. Set actual values in
each Lambda's environment-variable configuration. Creating a local
.env file does not automatically configure AWS Lambda.

## Verification

- [Functional tests](../../evidence/test-functional.md)
- [Security tests](../../evidence/test-security.md)
- [Backend tests](../../evidence/test-backend.md)
- [Analytics integration](../../evidence/test-analytics-cloud.md)

Record actual results and distinguish local mock tests from
requests made to the deployed AWS backend.

## Limitations

The frontend requires local setup. Cloud availability depends on
the AWS Academy environment. The prototype uses LabRole and does
not claim verified least-privilege IAM permissions.

Passwords, AWS keys or authentication tokens are not included in
configuration documents or submission evidence.
