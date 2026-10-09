# Lambda configuration

Recorded on: 9 October 2026
Region: us-east-1

| Function | Purpose | Runtime | Handler | Memory | Timeout | Role |
|---|---|---|---|---|---|---|
| roomly-booking-api | Booking, session and room management | Python 3.13 | lambda_handler.lambda_handler | 256 MB | 15secs | LabRole  |
| roomly-get-analytics | Reads historical analytics from S3 | Python 3.14  | lambda_function.lambda_handler | 128 MB | 10secs | LabRole  |
| roomly-get-rooms | Reads room records from the DynamoDB Rooms table and returns them as JSON for the room-list interface. | Python 3.13 | lambda_function.lambda_handler | 128 MB | 3secs | LabRole  |

## Environment variables

The booking function `roomly-booking-api` uses:

| Variable | Value | Purpose |
|---|---|---|
| `ROOMS_TABLE` | `Rooms` | Stores room information |
| `USERS_TABLE` | `RoomlyUsers` | Stores application users and access permissions |
| `BOOKINGS_TABLE` | `RoomlyBookings` | Stores booking records |
| `RESERVATIONS_TABLE` | `RoomlyReservations` | Stores room/participant reservation locks and system records |
| `AUTH_ISSUER` | `https://cognito-idp.us-east-1.amazonaws.com/us-east-1_EtQjacsSX` | Expected issuer of the authenticated identity |

The analytics function `roomly-get-analytics` uses:

| Variable | Value | Purpose |
|---|---|---|
| `ANALYTICS_BUCKET` | `roomly-analytics-2026-11` | Identifies the S3 bucket containing historical analytics outputs |

These application settings contain no passwords or AWS access keys. Lambda obtains permission to access AWS services through its execution role.

## Dependencies

### Booking Lambda

The booking function uses:

- `boto3` — accesses DynamoDB.
- `botocore` — handles AWS service exceptions.
- Python standard-library modules: `base64`, `datetime`, `decimal`, `hashlib`, `json`, `logging`, `os`, `re` and `secrets`.

Its application files are:

- `lambda_handler.py`
- `dynamodbService.py`

The deployed Python Lambda runtime supplies Boto3 and Botocore. Standard-library modules do not require separate installation. For running the cloud backend outside Lambda, Boto3 must be installed.

Historical analytics dependencies, such as pandas and matplotlib, belong to the offline analytics notebook. They are not dependencies of the booking Lambda.

## Deployment

### Booking function packaging

Package these two files at the root of the deployment ZIP:

```text
roomly-booking-api.zip
├── lambda_handler.py
└── dynamodbService.py
```

Do not place them inside an additional `backend` or `src` folder within the ZIP.

The configured handler is:

```text
lambda_handler.lambda_handler
```

The first part identifies `lambda_handler.py`; the second identifies the Python function called by Lambda.

### Upload and configuration

1. Open AWS Lambda and select `roomly-booking-api`.
2. Upload the deployment ZIP through the function's code upload option.
3. Check that both Python files appear at the root of the code source.
4. Confirm the runtime and handler in Runtime settings.
5. Configure the application environment variables listed above.
6. Confirm the execution role can access the required DynamoDB tables and write logs.
7. Wait until the function update completes before testing.
8. Confirm the relevant API Gateway routes integrate with this function.

### Verification

Use Roomly to perform an authenticated request and confirm:

- `GET /session` returns the signed-in application user.
- A valid booking is saved and remains visible after refreshing.
- Cancelling that booking releases the slot.
- A student request to `GET /admin/rooms` returns HTTP 403.
- An administrator request to the same endpoint returns HTTP 200.

Record the actual results, test date and evidence paths in the corresponding test documents. Inspect CloudWatch logs if a request fails.d.
