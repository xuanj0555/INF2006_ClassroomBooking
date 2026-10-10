# S3 Object Version Recovery Test

## Configuration
- Bucket: roomly-analytics-2026-11
- Object key: evidence-tests/recovery-test.txt
- Mechanism: S3 Versioning

## Procedure
1. Uploaded the initial text file.
2. Changed its contents and uploaded it to the same object key.
3. Enabled Show versions and observed two different version IDs.
4. Downloaded the earlier version and checked its contents.
5. Downloaded the current version and checked its contents.

## Results
- Two stored versions: PASS
- Expected earlier content: version one
- Actual downloaded earlier content: version one
- Expected current content: version two
- Actual downloaded current content: version two
- Earlier-version retrieval: PASS
- Test date: 9 October 2026

## Evidence
- evidence/s3-object-versions.png

## Conclusion and scope

The test successfully retrieved an earlier S3 object version and verified its original contents. This demonstrates recoverability through S3 versioning.

Restoration of that version as the current object was not tested. This test covers S3 objects only; it does not demonstrate recovery of DynamoDB data or the entire application.
