# AI Use Declaration

## Project

**Project:** Roomly – Campus Room Booking Service  
**Group:** P2-GROUP-01

## AI Tools Used

The team used generative AI tools, primarily OpenAI ChatGPT, as an assistance tool during the development and documentation of the project.

AI was used as a supporting tool and was not treated as an authoritative source. Team members reviewed, tested and verified AI-assisted suggestions before including them in the project.

## Where AI Was Used

### 1. Backend Development

ChatGPT was used by the backend member to assist with:

- Understanding and improving booking validation logic.
- Reviewing possible edge cases in room and participant conflicts.
- Suggesting approaches for transaction handling and repeated booking requests.
- Helping design and review automated backend tests.
- Debugging Python errors and test failures.
- Reviewing DynamoDB-related implementation ideas.
- Improving backend documentation and booking rules documentation.

AI-generated suggestions were reviewed against the actual project requirements and existing source code. Backend behaviour was verified through automated tests and manual checking.

### 2. Frontend Support

ChatGPT was used as a supporting tool when reviewing frontend issues and debugging presentation problems.

For example, AI assistance was used to identify CSS alignment issues in the participant selection interface and suggest targeted CSS changes.

The team tested the resulting changes in the local frontend before treating them as part of the project.

### 3. Documentation and Report Writing

ChatGPT was used to help:

- Organise and improve technical explanations.
- Draft and refine sections of project documentation.
- Review wording for clarity.
- Structure the project manifest and contribution documentation.
- Help prepare individual reflection drafts.

Team members reviewed the generated content and adjusted it to reflect the actual work completed by the team.

### 4. Debugging and Problem Investigation

ChatGPT was also used to help interpret error messages and identify possible causes during development.

For example, when the deployed Roomly application returned a `GET /session` HTTP 500 error after Cognito sign-in, AI assistance was used to explain the likely interaction between Cognito, API Gateway and the backend Lambda. The team was advised to verify the actual cause using the AWS/CloudWatch logs rather than treating the AI explanation as proof.

## Verification Process

AI-generated code and recommendations were not accepted automatically.

The team used the following verification process:

1. Compare the suggestion against the official INF2006 project requirements.
2. Check that the proposed change matches the existing Roomly architecture and code.
3. Run the relevant automated tests.
4. Perform manual testing where appropriate.
5. Review the output with the relevant team member responsible for the component.
6. Remove or modify suggestions that were not supported by the actual implementation.

For backend changes, automated testing was used extensively to verify booking conflicts, participant validation, capacity, booking limits, cancellation, authorisation, check-in and other edge cases.

For cloud-related behaviour, the team relied on actual AWS configuration, deployed behaviour and cloud logs rather than treating AI-generated explanations as evidence.

## Sources and Baselines

The project uses the official INF2006 Team Project Brief as the main source for project requirements and submission expectations.

The analytics component uses the historical room reservation dataset identified in the project report:

**Aceeedev, "University Library Room Reservations," Kaggle.**

The analytics documentation explains the dataset cleaning, fields, limitations and responsible-use considerations.

The project does not use AI-generated predictions as part of the room booking decision process. The analytics component is descriptive and is used to understand historical room reservation demand.

## Open-Source Libraries and Software

The project uses standard open-source software libraries and frameworks required by the implementation, including Python and relevant Python packages used by the backend and analytics components.

Third-party packages are installed through the project's dependency files where applicable. Their original licences remain applicable and are not claimed as original work by the team.

The team did not intentionally include proprietary code, credentials, private datasets or confidential information in the submission.

## Data and Privacy

The project uses synthetic demonstration users, rooms and booking data for the live Roomly prototype.

The historical analytics dataset does not contain personal user identities used by the live booking system. The project keeps historical room identifiers separate from the fictional demonstration rooms used by the application.

No passwords, AWS access keys, authentication tokens or other private credentials are included in the submission.

## Team Verification

All AI-assisted material was reviewed by the team member responsible for the relevant component.

The team verified that:

- AI-assisted backend code was tested before inclusion.
- AI-assisted frontend changes were manually checked.
- Technical claims were compared against the actual implementation.
- Analytics claims were checked against the processed dataset and validation results.
- AI-assisted documentation was reviewed against the final project.
- Unsupported AI-generated claims were removed or corrected.

AI was used as an assistance and productivity tool. Final responsibility for the submitted code, documentation, evidence and technical claims remains with the project team.

## Declaration

We confirm that AI tools were used during the development and documentation of this project and that their use has been declared above.

AI-generated suggestions were reviewed and verified by the team before being included in the final submission. The team takes responsibility for the correctness, testing and final content of the submitted project.