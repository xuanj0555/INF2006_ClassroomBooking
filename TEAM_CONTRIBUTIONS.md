# Team Contributions

## Project

**Project:** Roomly: Campus Room Booking with Historical Reservation Analytics  
**Group:** GROUP-G11

## Contribution Matrix

| Member | Student ID | GitHub Username | Role | Artefacts / Contributions | Test / Evidence Ownership |
|---|---|---|---|---|---|
| Sharlene | 2503489 | sharlene-04 | Frontend and User Experience | Frontend, administrator interface and dashboard; UI and authentication test records | Functional UI and authentication UI tests |
| Stanberley | 2501376 | Stanberley | Booking Backend and Validation | Booking services, validation, DynamoDB improvements, architecture diagram and backend test dependencies | Automated backend tests and booking conflict test records |
| Shermaine | 2501469 | xuanj0555 | AWS and Cloud Integration | AWS deployment and integration, Lambda handlers, Cognito integration, analytics permission update, infrastructure documentation and project manifest | Deployed functional and security tests, S3 version retrieval and CloudWatch monitoring |
| Yuchen | 2503041 | weiyuchen83 | Data Preparation and Analytics | Dataset cleaning, preparation script, data dictionary, analysis notebook, reproduction script and exported analytics outputs | Dataset preparation and analytics validation records |

## Representative Commits

These commits provide examples of recorded contributions. They are not an exhaustive list or a measure of each member’s total effort.

| Member | Commit | Recorded Work |
|---|---|---|
| Sharlene | `be93c2d` | Updated administrator and user interface, including the dashboard |
| Sharlene | `4322017` | Added `evidence/test-ui.md` and `evidence/test-auth-ui.md` |
| Stanberley | `5c5050e` | Implemented the booking backend |
| Stanberley | `92f9f34` | Improved backend and DynamoDB services and their automated tests |
| Stanberley | `d7e6707` | Updated the architecture diagram and added backend test dependencies |
| Shermaine | `f015df8` | Integrated the application with AWS services |
| Shermaine | `adf6196` | Updated analytics authorisation and added analytics security tests |
| Shermaine | `65c3ee4` | Added CloudWatch session-log and error-search screenshots |
| Yuchen | `3404575` | Added reservation-demand analysis and exported analytics outputs |
| Yuchen | `6345580` | Added preparation and reproduction scripts and refined validation records |

Commit authorship identifies who committed a change. Where a member uploaded shared work, the contribution descriptions credit the person who produced it. AWS console configuration, testing and report writing are also supported by documentation and evidence rather than commit counts alone.

## Individual Contributions

### Sharlene – Frontend and User Experience

I was responsible for Roomly’s frontend implementation and user experience. My work included room selection, the booking interface, participant selection, administrator screens and the analytics dashboard under `src/frontend/`.

I coordinated frontend requests and responses with the backend so that users could interact with the booking system through the website.

I prepared the functional UI and authentication UI test records in `evidence/test-ui.md` and `evidence/test-auth-ui.md`. These records distinguish completed checks from partial or untested behaviour.

### Stanberley – Booking Backend and Validation

I was responsible for the booking backend and validation rules. My work covered users, rooms, bookings and participants, including participant validation, duplicate participant rejection, automatic organiser inclusion, room capacity, booking limits, room conflicts and participant conflicts.

I implemented booking creation, cancellation and reservation handling, including releasing room and participant reservations when a booking is cancelled. The DynamoDB implementation uses transactional operations to prevent partial updates.

Additional work included authorisation checks, check-in validation, room-number generation, DynamoDB service improvements and automated backend tests. I also maintained the architecture diagram and backend test setup documentation.

The backend evidence distinguishes local and mock tests from deployed AWS checks. Cloud conflict and concurrency checks without recorded results are successful.

### Shermaine – AWS and Cloud Integration

I was responsible for configuring and integrating Roomly’s AWS backend with the locally served frontend. My work included Amazon API Gateway, AWS Lambda, DynamoDB, Amazon Cognito and the private S3 analytics bucket.

I configured Cognito sign-in and the API Gateway JWT authorizer, and documented the application’s identity mapping and cloud configuration. I integrated Yuchen’s historical analytics outputs with S3, the analytics Lambda and the website, and compared the returned metrics with the saved outputs.

I deployed updated Lambda packages and verified administrator room creation with an automatically assigned room ID. With AI assistance, I updated and deployed the analytics administrator check after testing revealed that students could retrieve analytics.

I performed and documented deployed functional and security tests covering booking persistence, cancellation and slot release, unauthenticated access, student access to administrative endpoints, room creation and editing, unauthorised cancellation, booking privacy and analytics permissions. After the analytics permission update, I recorded student access returning HTTP 403 and administrator access returning HTTP 200.

I documented retrieval of an earlier S3 object version and collected CloudWatch evidence for a successful `GET /session` request and an HTTP 500 log search. The evidence distinguishes version retrieval from restoration and does not claim whole-application recovery or performance under load.

I maintained the infrastructure configuration documents, deployment record, security and monitoring evidence, startup instructions and project manifest, and helped align the report with the implemented system and supporting evidence.

On 11 October 2026, I completed the full analytics reproduction test in a newly created Python environment on macOS. The workflow regenerated the cleaned dataset, executed the notebook and checked the expected output files, finishing with exit status 0. I also verified that the Kaggle source page lists the dataset licence as MIT and collected supporting screenshot evidence.

### Yuchen – Data Preparation and Analytics

I was responsible for preparing the historical reservation dataset and implementing the descriptive analytics.

My work included dataset cleaning, timestamp-derived duration calculations, documented exclusions, preservation of room identifiers as text and preparation of `data/reservations_cleaned_newversion.csv`. I added `data/prepare_reservations.py` to reproduce the cleaning process and maintained the dataset documentation and data dictionary.

I implemented `analytics/reservation_analysis.ipynb` to calculate reservation counts by room, weekday and start hour, reserved hours and duration statistics. I exported the four CSV and JSON outputs used by the cloud analytics service.

I added `analytics/reproduce.py` to coordinate dataset preparation, notebook execution and output-file checks, together with dependency and setup instructions.

I recorded dataset and analytics validation results in `evidence/test-data-ai.md`, including raw-to-cleaned totals, grouped counts, a manual reserved-hours calculation and independent comparisons with the saved cloud response.

These results describe historical reservation demand. They do not establish attendance, physical occupancy or future demand. Shermaine subsequently verified successful completion of the full workflow in a separate Python environment on 11 October 2026. The execution output is saved in evidence/analytics-reproduction-2026-10-11.txt.

## Team Collaboration

The team divided responsibilities between frontend development, booking backend implementation, AWS integration and historical analytics.

Members coordinated API request formats, response fields and data definitions to connect these components. Shared files were sometimes updated by more than one member, so responsibilities overlap where integration required joint work.

The historical analytics dataset remains separate from the live application’s rooms, users, bookings and attendance records.

## Individual Reflections

### Sharlene

Working on the frontend helped me understand that a usable interface depends on coordination with backend and cloud services. I learnt to align requests, responses and user-facing states with the application’s behaviour, and to record which interface checks had actually been completed.

### Stanberley

Working on the backend showed me how much validation is needed to make a booking system reliable. I had to consider conflicts, cancellation, reservation release, capacity and booking limits. I also learnt to distinguish what local or mock tests demonstrate from what must be verified against the deployed AWS system.

### Shermaine

Working on AWS integration gave me practical experience connecting API Gateway, Lambda, DynamoDB, Cognito and S3. Testing revealed how deployment configuration and backend permissions affect the website. I learnt to record observed results carefully, investigate failures across services and keep the documentation consistent with the deployed implementation.

### Yuchen

Working on the data and analytics component helped me understand the importance of reproducible cleaning and independent validation. I learnt to document exclusions, preserve identifiers correctly and distinguish reservation demand from actual occupancy. Adding preparation and reproduction scripts made the workflow easier for another person to follow, while documenting limitations helped avoid unsupported conclusions.

## Evidence and Verification Scope

Contribution descriptions are supported by Git history, source files, configuration documents and test records.

Key evidence includes:

- `evidence/test-ui.md`
- `evidence/test-auth-ui.md`
- `evidence/test-backend.md`
- `evidence/test-functional.md`
- `evidence/test-security.md`
- `evidence/test-data-ai.md`
- `evidence/test-analytics-cloud.md`
- `evidence/test-resilience.md`
- `evidence/monitoring.md`
- `evidence/deployment.md`

AI assistance is documented separately in `AI_USE_DECLARATION.md`.
