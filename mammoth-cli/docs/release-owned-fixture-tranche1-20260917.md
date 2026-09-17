# Release owned-fixture tranche 1 (2026-09-17)

Sanitized evidence for the first bounded Core run. CLI version: **1.1.3**.
The run used the saved release profile and project 3; no credentials are
recorded here.

| Case | Command | Result |
|---|---|---|
| 1 | `dataset create --project 3` (web URL fixture) | success; returned dataset ID 1, job ID 1, `ready` |
| 2 | `dataset get 1` | success; dataset ready, 51 rows |
| 3 | `dataset data 1` | success |
| 4 | `dataset list --project 3` | success; owned dataset present |
| 5 | `view list 1` | success; returned owned view ID 1 |
| 6 | `view get 1 1` | success; 19 data columns |
| 7 | `view preview 1 1` | success; 50 rows and 19 columns |
| 8 | `batch list 1` | success; 1 batch, 0 pending |
| 9 | `dataset delete 1 --yes` | success; returned deletion job ID 1 |
| 10 | `dataset list --project 3` | success; 0 datasets (cleanup postcondition) |

Saved response hashes (the create/get/data/list responses were not retained in
the shell transcript) are:

- `view get`: `f884ab8f3e533aa10d33115337dbc8374f897328a573ea4b163eed9fdf65c629`
- `view preview`: `b46bc57b1e5f40511bd361904416e5625ac85b8e3cecfa70633b5957a8d0ce3c`
- `batch list`: `f93be39b7c7f42134a7b6117532b08b8d0821eaede58206059632730439cc961`
- `dataset delete`: `60c64403560a46600bd31e84a886adb1746129818a410ac060b893625706a221`

Only returned dataset ID 1 was deleted; project 3 returned to its empty
baseline. No Full readiness claim is made.
