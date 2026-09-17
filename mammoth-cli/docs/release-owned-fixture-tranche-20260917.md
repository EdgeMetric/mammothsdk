# Release owned-fixture tranche (2026-09-17)

Sanitized evidence for the second bounded Core run. CLI version was **1.1.3**;
profile and endpoint details are intentionally omitted. All commands used
JSON output and `--no-input`.

| Case | Command | Result |
|---|---|---|
| 1 | `dataset create --project 3` (web URL fixture) | success; returned dataset ID 2, job ID 4, `ready` |
| 2 | `dataset get 2` | success |
| 3 | `batch list 2` | success; 1 batch (ID 2), 51 rows, 0 pending |
| 4 | `batch get 2 2` | success |
| 5 | `dataset file-settings get 2` | success |
| 6 | `view list 2` | success; owned dataview ID 2 |
| 7 | `view pipeline get 2` | success |
| 8 | `view pipeline items 2` | success; 0 items |
| 9 | `view task list 2` | success; 0 tasks |
| 10 | `view version list 2` | failed with `api_error`/`ValueError` envelope (release endpoint did not return a usable response) |
| 11 | `dataset delete 2 --yes` | success; returned deletion job ID 6 |
| 12 | `dataset list --project 3` | success; 0 datasets (cleanup postcondition) |

The only created resource was dataset 2 and its returned child resources (view
2 and batch 2); cleanup used the returned dataset ID and left project 3 at its
empty baseline. Output SHA-256 prefixes for the ten saved response files (the
create and version-list error were emitted on separate streams) are:

`540ec625b4712a2d`, `c9e3d8ee103a95c0`, `449e8fea138bbbcd`,
`13817f076b6c0b79`, `98bb43175376e0c2`, `24867024d472bd27`,
`21bcb9b1ae0d1da9`, `e808887b60695bce`, `511049a1fade5302`,
`5093410f00585276`.

No Full readiness claim is made. The version-list failure is recorded as an
undetermined release/API response issue; no CLI binding conclusion is drawn.

The later retained 1.1.5 dataset fixture (`live-evidence-20260917/dataset-next`)
also matched the oracle: dataset data returned 51 rows and 20 API columns,
and file-settings returned a structured `info` response. Dataset 4 cleanup
returned the project to zero datasets.

Diagnosis note: `view task list` calls the public SDK's
`PipelineAPI.list_tasks(dataview_id, dataset_id=None)`, which resolves the
same project/dataset/view route used by the successful pipeline-get call. The
captured release response is a generic `api_error` with `ValueError` and no
request ID or HTTP status, so this is recorded as an undetermined server/SDK
response issue; no CLI binding fix or readiness promotion is asserted.

The independent public-fixture oracle is retained at
`live-evidence-20260917/fixture-oracle.json`: 51 data rows, 19 source headers,
and the first row matches the public CSV. The captured dataset-data response
returned 51 rows and 20 API columns (19 source columns plus the system batch
column); the captured batch list reported 51 rows. These checks support only
bounded Partial evidence for dataset-data and batch-list.
