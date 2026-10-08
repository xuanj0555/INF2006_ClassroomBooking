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
- Expected earlier content: [enter initial text]
- Actual downloaded earlier content: [enter observed text]
- Expected current content: [enter newer text]
- Actual downloaded current content: [enter observed text]
- Earlier-version retrieval: [PASS only after checking]
- Test date: [date you completed the download checks]

## Evidence
- evidence/s3-object-versions.png

## Scope
This demonstrates retrieval of an earlier S3 object version
after an overwrite. It does not test whole-application recovery.
