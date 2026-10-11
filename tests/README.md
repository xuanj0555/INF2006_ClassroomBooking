# Roomly automated tests

Run commands from the repository root using Python 3. These tests exercise local services and mocked AWS dependencies. They do not send booking requests to the deployed AWS API or establish successful deployment.

## Setup

Create a separate environment and install the test dependency:

```bash
python3 -m venv .venv-tests
source .venv-tests/bin/activate
python -m pip install -r tests/requirements.txt
```

On Windows, use `py -m venv .venv-tests` and activate it in PowerShell with `.\.venv-tests\Scripts\Activate.ps1` before installing dependencies.

## Run the automated suite

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

A successful run ends with `OK` and exits with status 0. Record the actual test count and result when running; historical counts are not a guarantee for later revisions.

## Test coverage

| File | Scope |
|---|---|
| `test_backend.py` | Local SQLite booking rules, conflicts, limits, cancellation and check-in using a controlled clock and temporary databases. |
| `test_admin.py` | Local administrator permissions, room management and separation of historical analytics from live bookings. |
| `test_dynamodb_service.py` | DynamoDB service logic, reservation transactions, repeated requests and room-number generation using `fake_dynamodb.py`. |
| `test_analytics_security.py` | Analytics Lambda access checks with mocked user records and analytics reads. |

To run only one group:

```bash
python -m unittest discover -s tests -p 'test_dynamodb_service.py' -v
```

`fake_dynamodb.py` is a test helper. `viewDB.py` is a manual inspection utility, not part of the automated test suite.

## Historical analytics reproduction

This is a separate workflow requiring the analytics dependencies:

```bash
python -m pip install -r analytics/requirements.txt
python analytics/reproduce.py
```

The workflow regenerates the cleaned dataset, executes and saves the notebook, and checks for the four expected output files. It changes those generated files. Successful reproduction exits with status 0 and reports `PASS: analytics reproduced successfully`.

See [analytics instructions](../analytics/README.md) and [recorded data validation and reproduction result](../evidence/test-data-ai.md).

## Deployed and manual test records

- [Backend mock results and deployed booking checks](../evidence/test-backend.md)
- [Functional booking tests](../evidence/test-functional.md)
- [Security tests](../evidence/test-security.md)
- [Cloud analytics integration](../evidence/test-analytics-cloud.md)
- [Frontend UI tests](../evidence/test-ui.md)
- [Authentication UI tests](../evidence/test-auth-ui.md)
- [S3 version retrieval](../evidence/test-resilience.md)
- [CloudWatch monitoring](../evidence/monitoring.md)

The deployed sequential conflict tests and simultaneous identical-request test do not establish simultaneous cross-user competition, absence of partial database records, or campus-scale throughput. Keep those checks separate from mock-test results.

For starting the current frontend and signing in with Cognito, follow [START_HERE.md](../START_HERE.md).
