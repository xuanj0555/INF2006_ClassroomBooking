# Merge record

## Source and limitation
The requested Archive.zip (main) and archival2.zip (frontend) were not available at packaging time. The matching local Git repository was available, so this package was built from its main commit `5c5050e` and frontend commit `be93c2d`. It does not include any uncommitted changes that existed only in the missing ZIP files. The original repository was not edited or pushed.

## Resolutions
- Kept main's booking schema, participant records, ownership checks and transactional room/participant conflict prevention.
- Retained the frontend's admin navigation, room management and historical analytics screens; adapted them to main's canonical field names and account IDs.
- Added an admin service using the same database as booking operations; enforced admin permissions server-side.
- Added a participant picker and participant names to booking cards; corrected the demo login account values.
- Kept existing check-in/no-show behavior and tests from main.
- Escaped editable room and participant text when rendering HTML.
- Historical reservation rooms remain separate from fictional live application rooms. Historical demand is explicitly labelled as counts, not a validated prediction.
- Resolved test import capitalization and added three admin/history integration tests.
- Omitted the conflicting binary bookings.sqlite3 from the runnable project. A fresh roomly.sqlite3 is generated. Both original committed databases are provided unchanged in the separate database backup ZIP; their records were NOT merged because the schemas differ.

## GitHub pull request
The ZIP itself does not merge or close your GitHub pull request.
1. Keep a backup of your current folder and any uncommitted changes.
2. In your existing Git checkout, select the frontend branch and merge the latest main into it using GitHub Desktop.
3. Compare your current branches with the source commits above. If either has advanced, do not overwrite newer work with this package; those changes need another review.
4. For the matching versions, copy the combined src/, tests/, data/room_capacity.csv, .gitignore, START_HERE.md and MERGE_NOTES.md into that checkout, replacing the corresponding files. Keep your .git folder.
5. After backing it up, remove the conflicted bookings.sqlite3 from Git tracking (`git rm --cached bookings.sqlite3`). The replacement app uses a fresh roomly.sqlite3. Do not upload the database backups.
6. Review the changed files, run the tests and the browser checks in START_HERE.md, then mark conflicts resolved and commit the merge.
7. Push frontend. Review the pull request, then merge it into main when checks pass.

## AWS follow-up
The source branches use /api on the local Python server. This package does not silently replace that with the earlier GET /rooms AWS endpoint: booking availability, rooms and writes must use one consistent backend. Authentication, protected booking Lambda routes, DynamoDB transactional writes and deployed frontend configuration remain separate integration work.
