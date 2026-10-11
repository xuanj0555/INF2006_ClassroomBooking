# Start Roomly

## Requirements

- Python 3 installed.
- The project downloaded and extracted.
- Internet access and an available AWS backend.
- An assigned Cognito test account mapped to an active Roomly user.

## Start the website

1. Open a terminal in the project root.
2. Run the command for your operating system.

Mac:

    python3 -m http.server 8766 --bind 127.0.0.1 --directory src/frontend

Windows:

    py -m http.server 8766 --bind 127.0.0.1 --directory src/frontend

3. Open http://127.0.0.1:8766/
4. Sign in using your assigned Cognito test account.
5. Keep the terminal open while using Roomly.

Use this exact address because it matches the configured Cognito
callback and sign-out URL.

To stop the frontend, press Control+C in the terminal.

## How this version works

The local server serves the frontend files. Application requests
go to API Gateway and the AWS Lambda backend. DynamoDB stores
shared users, rooms, bookings and reservation records.

Historical analytics are returned by a separate Lambda reading
prepared output files from a private S3 bucket.

Do not use the older SQLite server or demo-account selection
instructions to start the current Cognito/AWS website.

## Troubleshooting

If Python is unavailable, install Python 3 and reopen the terminal.

If port 8766 is occupied, stop the existing server using that port
before starting another instance.

If the page opens but requests fail, confirm internet access,
sign in again, and check the AWS deployment configuration.
The frontend server alone does not provide the AWS backend.

## Further instructions

- [User guide](USER_GUIDE.md)
- [Infrastructure setup](src/infrastructure/README.md)
- [Deployment record](evidence/deployment.md)
