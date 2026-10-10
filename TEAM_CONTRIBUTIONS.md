# Team Contributions

## Project

**Project:** Roomly – Campus Room Booking Service  
**Group:** P2-GROUP-01

## Contribution Matrix

| Member | Student ID | Role | Artefacts / Commits | Test / Evidence Ownership |
|---|---|---|---|---|
| Sharlene | 2503489 | Frontend and User Experience | `src/frontend/*` | Functional UI test |
| Stanberley | 2501376 | Booking Backend and Validation | `src/backend/*`, architecture diagram | Booking Conflict test |
| Shermaine | 2501469 | AWS and Cloud Integration | `src/infrastructure/*`, Rooms table, get-rooms Lambda, API Gateway | Cloud / Security test |
| Yuchen | 2503041 | Data and Analytics | `analytics/*` | Data/AI validation test |

## Individual Contributions

### Sharlene – Frontend and User Experience

Sharlene was responsible for the frontend implementation and user experience of Roomly. Her work included the room selection, booking interface, participant selection and analytics-related frontend screens under `src/frontend/`. She coordinated the frontend request and response formats with the backend so that the website could communicate with the booking API.

Her testing responsibility was the functional UI workflow, including checking that users could navigate the booking process and interact with the main booking features.

### Stanberley – Booking Backend and Validation

Stanberley was responsible for the backend booking logic and validation. His work covered the logical handling of users, rooms, bookings and participants, together with booking validation rules such as participant validation, duplicate participant checking, automatic inclusion of the organiser, room capacity, organiser booking limits, room conflicts and participant conflicts.

She also worked on booking creation, cancellation and reservation handling, including releasing room and participant reservations when a booking is cancelled. The backend was designed to use transactional operations to prevent partial booking updates and to handle repeated or conflicting booking requests.

Additional backend work included DynamoDB service integration, reservation records, concurrent booking handling, authorisation checks, check-in validation, room-number generation and automated backend testing. The backend test suite covers successful and rejected booking scenarios, room and participant conflicts, cancellation, capacity, booking limits, check-in timing and other edge cases.

Stanberley also prepared and maintained the architecture diagram and was responsible for the Booking Conflict test evidence.

### Shermaine – AWS and Cloud Integration

Shermaine was responsible for the AWS and cloud integration work. This included the AWS infrastructure configuration, Rooms table, room-list Lambda function and API Gateway integration.

She also worked on cloud authentication and integration with Amazon Cognito, together with the configuration required for the frontend and backend to communicate with the deployed AWS services.

Her testing responsibility was the Cloud / Security test, including checking cloud endpoint behaviour, authentication and relevant access controls.

### Yuchen – Data and Analytics

Yuchen was responsible for the data and analytics component under `analytics/`. This included cleaning and preparing the historical room reservation dataset and producing the reservation-demand analysis.

The analysis examines reservation counts by room, weekday and start hour, reserved hours and reservation duration statistics. The results are intended to help understand historical room usage patterns rather than make automated booking decisions.

Yuchen was responsible for the Data/AI validation test and for verifying that the calculated analytics results matched expected values from the processed dataset.

## Team Collaboration

The team divided the project into frontend, backend, cloud integration and data/analytics responsibilities, while coordinating the interfaces between these components.

The team used shared API expectations and agreed data field names so that the frontend, backend and cloud components could be integrated consistently. Changes affecting shared functionality were tested before being treated as part of the final project.

Team members also reviewed each other's work where necessary, particularly when integrating the frontend with the AWS backend and when checking that the architecture and evidence matched the implemented system.

## Individual Reflections

### Sharlene

Working on the frontend gave me experience in building the user-facing part of a cloud application while also having to coordinate closely with the backend and AWS components. I learnt that frontend development is not only about making the interface look good, but also making sure that the requests, responses and error states match what the backend actually provides.

### Stanberley

Working on the backend helped me understand how much detail is involved in making a booking system reliable. I worked on validation, conflicts, cancellation, reservations and automated testing, and I had to consider situations such as two users trying to book the same slot at the same time. I also learnt that local tests and a deployed AWS system can behave differently, so debugging requires looking at the whole system rather than only my own code.

### Shermaine

Working on AWS and cloud integration gave me practical experience connecting different managed cloud services together. I learnt more about API Gateway, Lambda, DynamoDB and Cognito, as well as the importance of authentication, permissions and deployment configuration. I also learnt that cloud integration requires careful testing because a problem in one service can affect the entire application.

### Yuchen

Working on the data and analytics component helped me understand how raw historical data needs to be cleaned and validated before it can be used meaningfully. I learnt how to calculate and verify room usage metrics and how to present the results in a way that supports the project without making unsupported predictions. It also showed me the importance of documenting the data source, preprocessing and limitations of the analysis.

## Team Verification

Each member reviewed their assigned artefacts and test/evidence ownership before submission. The team also reviewed the final project structure, evidence paths and contribution records to ensure that the contribution descriptions correspond to the work included in the submission.