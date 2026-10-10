# IAM Access and Permissions

Recorded on: 10 October 2026

## Execution roles

The deployment uses the AWS Academy LabRole where configured.
Each function's execution role can be checked under
Lambda → Configuration → Permissions.

| Function | Execution role |
|---|---|
| roomly-booking-api | LabRole |
| roomly-get-analytics | LabRole |
| roomly-get-rooms | LabRole |

Lambda obtains AWS service credentials through its execution
role. AWS access keys are not embedded in the frontend or
application source.

## Application access requirements

| Component | Required access | Resources |
|---|---|---|
| Booking Lambda | Read application records and perform transactional booking, cancellation and room-management updates | Rooms, RoomlyUsers, RoomlyBookings and RoomlyReservations |
| Analytics Lambda | Read historical analytics output objects | Four objects under analytics/output/ in roomly-analytics-2026-11 |
| Lambda logging | Create log streams and write execution logs | Relevant CloudWatch log groups |

These describe the application's access requirements.
They are not a claim that the attached IAM policies are
restricted to exactly these resources.

## Verified policy configuration

Function: roomly-booking-api
Execution role: LabRole
Verified on: 10 October 2026

Attached policy names: Not verified. The console could not
retrieve policy details because the lab account was explicitly
denied iam:GetPolicy.

Policy scope: Not verified. The allowed actions and resource
restrictions could not be inspected with the available permissions.

This confirms a restriction on inspecting IAM policies.
It does not establish that LabRole follows least privilege.

## Application authorisation

Cognito authenticates Roomly users, and API Gateway validates
tokens on routes with the JWT authorizer attached.

The booking backend checks application permissions separately.
Administrative room operations require administrator access.
Cancellation requires the booking organiser or an authorised
administrator.

These checks control application users. They do not replace
IAM restrictions on the Lambda execution role.

## Limitations and improvements

LabRole is a shared laboratory role. Its permissions may be
broader than those required by Roomly. This submission does
not claim that a custom least-privilege execution role has
been implemented.

For production, separate execution roles should restrict
each function to its required resources. The analytics
function should have read access to the required S3 objects,
while the booking function should have the necessary access
to the four application tables. Logging permissions should
also be limited appropriately.

Any restriction on creating or modifying IAM roles should
be documented only if confirmed in the lab instructions
or by an actual permission-denied result.
