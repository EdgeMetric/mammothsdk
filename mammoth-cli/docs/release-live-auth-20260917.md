# Release live-auth verification (2026-09-17)

This record contains no credentials or credential-derived values. Commands
were run with the saved `expanded-live` profile against the release endpoint.

Verified with `mammoth-cli` **1.1.3**:

- `mammoth doctor`: passed all five checks (profile, credentials, endpoint,
  and authenticated connection).
- `mammoth project list`: returned **1** project, project **3** (`API
  Tests_project`) in workspace **4**.
- `mammoth dataset list --project 3`: returned **0** datasets.
- `mammoth file list --project 3`, `folder list --project 3`, `project
  checkpoint list 3`, and `project data-check list 3`: each returned **0**
  resources.
- `mammoth dashboard list --project 3`: succeeded and returned **0**
  dashboards (the endpoint is workspace-scoped in the response).
- `mammoth context project use 3`, `project get 3`, `project
  pending-changes 3`, and `project resource-status 3`: all succeeded;
  pending items and resource status were empty.

The project-3 dataset count is zero, so dataset **120** is not present in this
scope and its preservation cannot be assessed from this run. No live resource
was left behind.

## Disposable Core tranche

Using only returned IDs, one web-URL dataset was created (`dataset_id=1`,
`job_id=1`, ready), then verified and removed. The owned dataset produced one
dataview and one batch. Successful read/postcondition cases were:

- dataset get, dataset data, dataset list;
- view list, view get, and view preview (50 preview rows, 19 columns); and
- batch list (1 batch, 0 pending batches).

Dataset deletion returned `job_id=1`; a final dataset list returned **0**.
This is 10 successful live cases in the disposable tranche (including create,
delete, and final absence), with no binding or authorization defect observed.
