# Backend-defect reproduction handover — release, CLI 2.0.15

Fixture: project 24 (`cli-backend-repro-20260918`, workspace 4) → dataset 54
(`stores.csv`, 20 rows) → view 76 (columns: `column_1`=store_id NUMERIC,
`column_2`=store_name TEXT, `column_3`=region TEXT, `column_4`=opened_on DATE).
All commands run as `<venv>/bin/mammoth ... --profile release --output json
--no-input` (plus `--yes`/`--confirm` where required). No `auth`/`config`
commands were run; no credentials were read, printed, or handled. Only
resources created in this session were touched; project 3 and the pre-existing
project 23 were never read or written.

---

## 1. `view.checkpoint.get`

- **Route:** `GET /workspaces/4/projects/24/datasets/54/dataviews/76/pipeline/checkpoints/{id}`
- **Request:** none (plain GET), checkpoint id created moments earlier by `view.checkpoint.create` (`checkpoint_id: 2`).
- **Response:** HTTP 500, `response_body: {}`, `request_id: null`, no backend error code surfaced.
- **Reproduction:**
  ```
  mammoth view checkpoint create 76 54 --project 24 --profile release --output json --no-input \
    --input '{"dataset_id":54,"body":{"checkpoint_name":"repro-checkpoint","checkpoint_type":"alert","pinned_to_end":true}}'
  mammoth view checkpoint get 76 2 --project 24 --profile release --output json --no-input \
    --input '{"dataset_id":54}'
  ```
- **Alternative tried:** omitted `dataset_id` from `--input` (letting the CLI discover the parent) → identical HTTP 500 on the identical endpoint. Input shape is not the variable.
- **Classification:** `backend` — a bare GET immediately after a successful create, empty 500 body, unaffected by input shape.
- **Suggested fix owner:** backend (dataview pipeline / checkpoints service).

---

## 2. `view.checkpoint.update`

- **Route:** `PATCH /workspaces/4/projects/24/datasets/54/dataviews/76/pipeline/checkpoints/2`
- **Request:** `{"patches":[{"op":"command","path":"approve","value":null}]}` (this is the documented `runnable_example` verbatim).
- **Response:** HTTP 500, empty body, `request_id: null`, CLI correctly reported `outcome_unknown` (exit 7) rather than a false success.
- **Reproduction:**
  ```
  mammoth view checkpoint update 76 2 --project 24 --profile release --output json --no-input \
    --input '{"dataset_id":54,"body":{"patches":[{"op":"command","path":"approve","value":null}]}}'
  ```
- **Alternative tried:** same checkpoint, `path:"enable"` instead of `"approve"` (still `op:"command"`, `value:null`) → identical HTTP 500. Could not reconcile checkpoint 2's true state because `view.checkpoint.get` on the same checkpoint independently 500s (item 1), blocking verification entirely.
- **Classification:** `backend` — two different schema-legal patch bodies on the PATCH route both 500 identically; not input-shape sensitive.
- **Suggested fix owner:** backend (dataview pipeline / checkpoints service), plus consider making `view.checkpoint.get` reliable so callers can reconcile PATCH outcomes.

---

## 3. `view.data-check.update`

- **Route:** `PATCH /workspaces/4/projects/24/datasets/54/dataviews/76/pipeline/data-checks/3`
- **Request:** `{"patches":[{"op":"command","path":"enable","value":null}]}`
- **Response:** HTTP 500, empty body, `request_id: null`, `outcome_unknown`.
- **Reproduction:**
  ```
  mammoth view data-check create 76 54 --project 24 --profile release --output json --no-input \
    --input '{"dataset_id":54,"body":{"name":"repro-check","checks":[{"check_type":"null_percentage","config":{"column":"store_name","condition":"lt"}}],"pinned_to_end":true}}'
  mammoth view data-check update 76 3 --project 24 --profile release --output json --no-input \
    --input '{"dataset_id":54,"body":{"patches":[{"op":"command","path":"enable","value":null}]}}'
  ```
- **Reconciliation:** `view data-check get 76 3` afterward showed `enabled:true`, `updated_at:null` — the patch did not commit.
- **Alternatives tried:** (a) `op:"replace",path:"enable"` (no value) → HTTP 400 4GENR007 "patches.0.value: Field required"; (b) `op:"replace",path:"enable",value:null` → HTTP 400 4GENR007 "For op PatchOps.REPLACE, path must be one of [DataCheckPatchPath.SPEC]". This backend validation message proves `op:"command"` is the *only* schema-legal combination for `path:"enable"` — there is no alternative client input that avoids the 500.
- **Classification:** `backend` — the single valid request for this operation crashes the server.
- **Suggested fix owner:** backend (dataview pipeline / data-checks service).

---

## 4. `view.derivative.data`

- **Route:** `POST /workspaces/4/projects/24/datasets/54/dataviews/76/derivatives/4/data`
- **Request:** `{"condition":{"FILTER_TYPE":"SHOW"}}` (documented `runnable_example` verbatim), against a freshly-created derivative (`SUM` of `column_1`/store_id).
- **Response:** HTTP 500, empty body, `request_id: null`, `outcome_unknown` (read-shaped POST, no state to reconcile).
- **Reproduction:**
  ```
  mammoth view derivative create 76 54 --project 24 --profile release --output json --no-input \
    --input '{"dataset_id":54,"body":{"param":{"METRIC":{"AS":"repro_metric","EXPRESSION":[{"TYPE":"FUNCTION","VALUE":{"ARGUMENT":"column_1","FUNCTION":"SUM"}}]}}}}'
  mammoth view derivative data 76 4 --project 24 --profile release --output json --no-input \
    --input '{"dataset_id":54,"body":{"condition":{"FILTER_TYPE":"SHOW"}}}'
  ```
- **Alternative tried:** richer condition with a `STRING_PROP` filter (`COLUMN:column_2,OPERATOR:CONTAINS,VALUE:Store`) → identical HTTP 500. A third probe with an empty body `{}` gave a *different* HTTP 400 4GENR007 referencing a bare `'data'` key (looks like an unhandled server-side KeyError, not a real field name), confirming the route inspects the body but breaks specifically once a well-formed condition is supplied.
- **Classification:** `backend` — two different well-formed condition bodies 500 identically.
- **Suggested fix owner:** backend (derivatives data-fetch service).

---

## 5. `view.export.create`

- **Route:** `POST /workspaces/4/projects/24/datasets/54/dataviews/76/actions` (job-based), `handler_type: csv_file`.
- **Request:** `{"export_spec":{"DATAVIEW_ID":76,"handler_type":"csv_file","trigger_type":"none","target_properties":{"file":"repro_export.csv","file_type":"csv","include_hidden":false,"is_format_set":true,"use_format":true,"destination":"local"},"additional_properties":{},"run_immediately":true}}`
- **Response:** CLI accepts the request (exit 0, job 358 accepted). `job get 358` → `status:"error"`, `response:{"error":{"message":"'destination'"}}` — a raw Python `KeyError` repr, not a structured message. `request_id: null`.
- **Reproduction:**
  ```
  mammoth view export create 76 --project 24 --profile release --output json --no-input --yes \
    --input '{"export_spec":{"DATAVIEW_ID":76,"handler_type":"csv_file","trigger_type":"none","target_properties":{"file":"repro_export.csv","file_type":"csv","include_hidden":false,"is_format_set":true,"use_format":true,"destination":"local"},"additional_properties":{},"run_immediately":true}}' --yes
  mammoth job get 358 --project 24 --profile release --output json --no-input
  ```
- **Diff against the typed route:** `mammoth schema get view.export.create` shows `target_properties` for `csv_file` resolves to `$defs.export_spec__S3TargetProperties`, whose *only* declared properties are `file, file_type, include_hidden, is_format_set, use_format` — **`destination` is not a documented field anywhere in the schema**, so there is no schema-legal way for a client to supply the field the backend's own error message complains about. `mammoth view export csv 76` (the typed shortcut, `confirmation:none`, no `export_spec` at all) succeeded immediately and wrote a real 20-row CSV (`dataview_54_76_export.csv`, byte-identical row count/columns to `stores.csv`). `view export list 76 54` returned `exports:[]` both before and after — the generic route's failed action is not a persisted export config, so there was nothing to diff at the list level; the real gap is in the schema (missing `destination` field), not the list.
- **Classification:** `backend` for the generic `csv_file` route (the field its error demands isn't exposed by its own contract); `client_docs` note: `view export csv` is the correct, working alternative and should be the documented path for CSV (already partially captured in `references/recipes/exports.md`).
- **Suggested fix owner:** backend (export handler dispatch for `csv_file`) to either accept/require `destination` in the schema or stop referencing it; docs owner to make the "use `view export csv`, not the generic route, for CSV" guidance more prominent.

---

## 6. `view.task.preview`

- **Route:** `POST /workspaces/4/projects/24/datasets/54/dataviews/76/pipeline/task_preview`
- **Request:** `{"task_spec":{"DATAVIEW_ID":76,"SEQUENCE_NUMBER":1,"COPY":{}}}` (documented `runnable_example` verbatim).
- **Response:** HTTP 400 5GENR010 `UNKNOWN_ERROR` "Unknown error occurred. Please contact support." wrapping `error_object:{code:720,message:"Source column not present."}`. `request_id: null`.
- **Reproduction:**
  ```
  mammoth view task preview 76 --project 24 --profile release --output json --no-input \
    --input '{"dataset_id":54,"task_spec":{"DATAVIEW_ID":76,"SEQUENCE_NUMBER":1,"COPY":{}}}'
  ```
- **Alternative tried:** `COPY:{"SOURCE_COLUMN":"column_1","NEW_COLUMN_NAME":"store_id_copy"}` using the **internal** column name (`column_1` = display name `store_id`, confirmed via `view list 76`) instead of a display name → **identical** error (same `code:720`/5GENR010). This rules out the display-name-vs-internal-name hypothesis the brief asked us to test: switching to internal names did not fix it.
- **Classification:** `backend` for the error-shaping defect — `task_spec` is fully freeform (`schema: additionalProperties:{}` object) with zero field-name guidance for `COPY` or any task type, so the CLI genuinely cannot tell a caller the right keys; independent of that, the backend wraps a real, specific, structured validation error (`code:720`) inside a generic "contact support" 5GENR010 envelope instead of surfacing it as an ordinary 400 (the way `4GENR007` routes do elsewhere). Whether some other undocumented `COPY` key name would succeed is **UNVERIFIED** — `task_spec`'s freeform schema gives no way to discover it without reading backend source, which was out of scope.
- **Suggested fix owner:** backend (raw task/pipeline preview route) to surface `code:720` as a normal validation error; docs owner to document `COPY`'s actual field names (`task_spec` freeform schema is a genuine gap).

---

## 7. `dataset.create-from-pdf`

- **Route:** `POST /workspaces/4/projects/24/datasets-from-pdf`
- **Request attempt 1:** `{"file_name":"sample.pdf"}` (file id 56, uploaded via `file upload`) → HTTP 400 4DSET053 `MUST_PROVIDE_TABLE_LIST_OR_PREVIEW`: "Either 'table_list' or 'is_preview_needed' must be provided." (clear, actionable, matches the item exactly).
- **Request attempt 2:** added `"is_preview_needed":true` → HTTP 400 4DTSTO003 `PDF_TABLES_DATASET_CREATION_FAILED`: "Unexpected errors while creating datasets of pdf tables". `request_id: null` both times.
- **Reproduction:**
  ```
  mammoth file upload ./sample.pdf --project 24 --profile release --output json --no-input
  mammoth dataset create-from-pdf 56 --project 24 --profile release --output json --no-input \
    --input '{"file_name":"sample.pdf"}'
  mammoth dataset create-from-pdf 56 --project 24 --profile release --output json --no-input \
    --input '{"file_name":"sample.pdf","is_preview_needed":true}'
  ```
- **Alternative tried:** the provided `sample.pdf` is a minimal synthetic PDF (plain text, no drawn table lines). To rule out "no real table in the fixture" as the sole explanation, hand-built a second PDF (`sample_table.pdf`, raw PDF byte construction, no external libraries available — `pip` and `reportlab`/`fpdf` were not available in the venv) containing an actual vector-drawn 3×4 grid (`m`/`l`/`S` line operators forming real cell borders) with aligned cell text, uploaded as file 57, and re-ran the identical `is_preview_needed:true` request → **identical** HTTP 400 4DTSTO003.
- **Classification:** `backend` — a structurally genuine table PDF fails with the exact same generic, non-diagnostic error as the minimal text-only PDF, ruling out "bad fixture" as the sole cause. The error message gives zero actionable diagnostic detail (no page/line info, no distinction between "no table found" and a parser failure) in either case.
- **Suggested fix owner:** backend (PDF table extraction service) — both for the underlying extraction/parsing behavior and for making `PDF_TABLES_DATASET_CREATION_FAILED` a diagnosable error.

---

## 8. `dashboard.template.create`

- **Route:** `POST /dashboards/v3/templates`
- **Fixture:** one blank dashboard, id 58, created via `dashboard create-blank` on view 76/dataset 54/project 24 (the only dashboard created in this session, per the one-dashboard limit).
- **Request:** `{"body":{"params":{"dashboard_id":58,"title":"repro-template-20260918"}}}`
- **Response:** HTTP 500, empty body, `request_id: null`, `outcome_unknown`.
- **Reproduction:**
  ```
  mammoth dashboard create-blank --project 24 --profile release --output json --no-input --yes \
    --input '{"params":{"dataview_id":76}}'
  mammoth dashboard template create --project 24 --profile release --output json --no-input \
    --input '{"body":{"params":{"dashboard_id":58,"title":"repro-template-20260918"}}}'
  ```
- **Reconciliation:** `dashboard template list` → `is_yours:true` templates = `[]` after the attempt — did not commit.
- **Alternative tried:** same `dashboard_id`, different `title`/`description` (`"repro-template-20260918-v2"`) → identical HTTP 500/`outcome_unknown`. Reconciled again: still no owned template.
- **Classification:** `backend` — two different request bodies against the same valid, freshly-created blank dashboard both 500 identically. Matches the `dashboard-reverify-20260918` finding exactly (both of its attempts also 500'd and did not commit).
- **Suggested fix owner:** backend (dashboard templates service).
- **Cleanup:** dashboard 58 was trashed (`dashboard trash 58`) then permanently deleted (`dashboard delete 58 --yes`) immediately after this test — both exit 0.

---

## 9. `ai.retention.condition`

- **Route:** `POST /workspaces/4/projects/24/sql_generation/retention_policy`
- **Request:** `{"mode":"generate","intent":"rows older than 90 days"}`
- **Response:** HTTP 403 4PERM001 `PERMISSION_UNDEFINED`, `error_object:{code:76,message:"Permissions have not been set correctly for this API, please contact Mammoth Help to report this error"}`. `request_id: null`.
- **Reproduction:**
  ```
  mammoth ai retention condition 54 --project 24 --profile release --output json --no-input \
    --input '{"mode":"generate","intent":"rows older than 90 days"}'
  ```
- **Alternative tried:** none — one attempt only, as instructed; this is a workspace/account entitlement gap, not something any client input can fix.
- **Classification:** `permission`.
- **Suggested fix owner:** account/workspace entitlement owner (Mammoth Help, per the error's own message) — the permission for this API needs to be provisioned for the workspace/API-key combination.

---

## 10. `view.ai.generation-info`

- **Route:** `GET /workspaces/4/projects/24/datasets/54/dataviews/76/data/generate`
- **Request:** `{"dataset_id":54}` (positional `view_id:76`).
- **Response:** HTTP 400 5GENR011 `NOT_IMPLEMENTED`: "Not implemented". `request_id: null`.
- **Reproduction:**
  ```
  mammoth view ai generation-info 76 --project 24 --profile release --output json --no-input \
    --input '{"dataset_id":54}'
  ```
- **Alternative tried:** none — one attempt only, as instructed; the backend explicitly self-reports the route as unimplemented, and there's no body variation to try on a GET.
- **Classification:** `backend` (route not implemented server-side).
- **Suggested fix owner:** backend (view AI generation-info route) — either implement it or have the CLI/docs mark it unsupported the way `dashboard.create` already is.

---

## IDs created and cleanup state

| Resource | ID | Cleanup |
|---|---|---|
| Project | `cli-backend-repro-20260918` → 24 | Deleted (`project delete 24 --yes` → HTTP 202, accepted) |
| Dataset | 54 (`stores.csv`) | Deleted via project 24 cascade |
| View | 76 | Deleted via project 24 cascade |
| Checkpoint | 2 (on view 76) | Deleted via project 24 cascade (final approval/enable state was never confirmable — `view.checkpoint.get`/`update` both 500) |
| Data check | 3 (on view 76) | Deleted via project 24 cascade |
| Derivative | 4 (on view 76) | Deleted via project 24 cascade |
| Files | 56 (`sample.pdf`), 57 (`sample_table.pdf`, hand-built) | Deleted via project 24 cascade |
| Dashboard | 58 | Explicitly trashed + permanently deleted before project deletion (both exit 0) |
| Export job | 358 (failed `csv_file` export action) | Not a deletable resource; no cleanup applicable |
| Local export artifact | `dataview_54_76_export.csv` (from `view export csv`) | Local file in the scratch directory only, not a remote resource; left in place as evidence |

## Final `project list`

```
mammoth project list --profile release --output json --no-input
```
```json
{
  "projects": [
    {"id": 3, "name": "API Tests_project"},
    {"id": 23, "name": "cli-reverify-215-20260918"}
  ]
}
```

Project 24 (created for this session) no longer appears — confirmed by direct
command output. **Note:** the brief expected only project 3 to remain, but
project 23 (`cli-reverify-215-20260918`) was already present in workspace 4
*before this session started* (visible in the very first `project list` call
made here, prior to creating project 24). It was not created by this session
and was never read or modified, per the hard rule against touching resources
not created here; its continued presence is a pre-existing condition, not
leftover from this repro run.

## Time-box

All 10 items were run within the 60-minute budget; nothing was recorded as
`not_run`.

## Addendum (operator, after the agent run) — `view.task.preview`

The documented `COPY: {}` placeholder was the CLI's fault: the backend COPY
param template is a list, `{"COPY": [{"SOURCE": "column_1", "AS": {"COLUMN":
"...", "TYPE": "NUMERIC", "INTERNAL_NAME": "column_9"}}], "VERSION": 2,
"DATAVIEW_ID": ..., "SEQUENCE_NUMBER": 1}` (the shape the SDK's typed
`copy_columns` builds). With that shape on a fresh fixture (project 25,
dataset 56, view 78; deleted afterwards) the preview request is accepted and a
`task_preview` job is created, which then fails on the backend with
`(builtins.TypeError) Object of type datetime is not JSON serializable` while
writing `future_requests.response` (job 379). Without `INTERNAL_NAME` the job
fails earlier with `'INTERNAL_NAME'` (job 377). Classification: CLI example
defect (fixed in 2.0.16) plus a backend serialization defect in the preview
response for views with a DATE column. Owner: backend (task_preview response
serialization).

## Addendum (operator, 2026-09-19) — all-text CSV never gets a view

- **Route:** `POST /workspaces/4/projects/{p}/files` → `GET .../datasets/{id}`; then `PATCH .../datasets/{id}/file-settings` (`understand_csv`).
- **Fixture:** project 36, `customers.csv` (3 rows; columns `customer_id`, `region`, both text) → datasets 74 and 75; `orders.csv` (numeric and date columns) → dataset 76. All deleted afterwards; `project list` = project 3 only.
- **Observed:** the all-text file reaches `status: "ready"` with `status_info.ready` = "This file has more than one plausible way to be read.", `file-settings get` shows `automation_possible: true`, `at_least_one_non_text_column_present: false`, and `view list` stays empty. `file-settings update` (with the detected settings, with and without `skip_auto_process_check: true`) returns a successful `understand_csv` job and a batch (row_count 3) but still no dataview. `orders.csv` in the same project got its view immediately.
- **Classification:** `backend` — `ready` is reported for a dataset that has not been processed into a view, and confirming the settings does not process it. Reference: `mvc-service/api/api/file/unprocessed.py` (`understand()`/`process()`), where the plausibility gate leaves the dataset without a view.
- **CLI side (2.0.18):** `file upload` now reports this state as `need_action` with `next_command: mammoth dataset file-settings get ID` instead of `ready`; `recipes/need-action.md` documents the stop condition.
- **Suggested fix owner:** backend (file understanding / auto-process) — either create the view when settings are confirmed or report the dataset as `need_action` rather than `ready`.

## Addendum (operator, 2026-09-19) — `clone_config_from` leaves the copy unreadable

- **Route:** `POST /workspaces/4/projects/38/datasets/80/dataviews` with `{"name": "clone-test", "clone_config_from": 96}` → job 520 (`clone_dataview`) → `success`; then `GET .../dataviews/99`.
- **Fixture:** project 38 (`dbg4-20260919`), dataset 80 (`orders_usd.csv`, 6 rows), source view 96 with two executed tasks (REPLACE, CONVERT). Copy = view 99. All deleted afterwards; `project list` = project 3 only.
- **Observed:** every `GET .../dataviews/99` answers HTTP 400 `4DTVW019 INVALID_RESPONSE_GENERATED` ("The response generated is invalid. Please try again later."), still five minutes after the clone job succeeded. `view task list 99` shows the copied tasks 48 (REPLACE) and 49 (CONVERT) in `status: added`, `pipeline get` shows `draft_mode: dirty`, `auto_run: false`, `execution_state: idle`. `view data get 99` fails (`get_dataview_data` job error `'NoneType' object has no attribute 'id'`); `view draft submit 99` fails on the same GET; `pipeline/rerun` rejects an empty body (`4GENR007 'data'`). The same symptoms appeared in the first golden run (view 92, project 37) after a REPLACE task on a column the platform had typed NUMERIC (`$1,234.56` is parsed as a number on upload).
- **Classification:** `backend` — a clone job that reports success hands back a dataview the API cannot serialise and whose pipeline is never run; `pipeline/items` on such a view also returned 403 `4PERM002` once (view 92).
- **CLI side (2.0.18):** recipes no longer build summaries on a `clone_from` copy (export the source rows, then pivot in place as the last step); `recovery.md` maps `4DTVW019` after `clone_from` to that path. `view create` now returns the new view's record (`id`, `dataset_id`) instead of `"<unserializable View>"`.
- **Suggested fix owner:** backend (dataview clone task: run or stage the copied pipeline and return a serialisable dataview).
