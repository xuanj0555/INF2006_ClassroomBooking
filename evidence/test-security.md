# Admin endpoint access test

Date: 9 October 2026
Endpoint: GET /admin/rooms
Objective: Verify that AWS restricts access to the admin room list.

Method:
1. Sign in as Test Student B and request the endpoint using its login token.
2. Request the endpoint without an Authorization header.
3. Sign in as Test Admin and request the endpoint using its login token.
4. Compare the returned HTTP statuses and response bodies.

| Account | Expected status | Actual status | Result |
|---|---|---|---|
| Test Student B | 403 | 403 | Pass |
| No token | 401 | 401 | Pass |
| Test Admin | 200 | 200 | Pass |

Observed responses:
- Student: `not_allowed` — `Administrator access required.`
- No token: `Unauthorized`
- Administrator: Room data returned successfully.

Evidence:
- `security-student-no-token-2026-10-09.png`
- `security-admin-2026-10-09.png`

Threat tested: A student bypassing the interface to access an admin API.

Conclusion: The deployed endpoint rejects unauthenticated requests
and denies student access while allowing administrator access.

Scope: This test verifies GET /admin/rooms only. It does not verify
room creation, room editing or analytics permissions.
