# Fixture-lifecycle sweep on release (CLI 2.0.18) — sweep-218

Owned project: `sweep-218-1224` (id **41**), created and fully torn down in this run.
Fixtures created/destroyed inside it: datasets **85** (fixture.csv), **86** (webhook-backing),
**87** (fixture2.csv); dataview **106**; and one instance each of webhook, automation, workflow,
snippet, template, parameter, view-checkpoint, view-data-check, view-derivative, batch.
No resource with `is_yours:false`, project 3, or the concurrent `golden-*` project/ids was read
for mutation or touched.

## Verdict counts

| verdict | count |
|---|---|
| ok | 59 |
| ok_empty | 14 |
| backend_error | 12 |
| cli_error | 4 |
| blocked_missing_fixture | 1 |
| skipped_out_of_scope | 1 |
| **total** | **91** |

## Full command log

| command_id | verdict | detail |
|---|---|---|
| `project.create` | ok | Created project id=41 name=sweep-218-1224. |
| `file.upload` | ok | Uploaded fixture.csv, returned dataset_id=85 with status need_action (file settings needed). |
| `dataset.file-settings.get` | ok | Read parse info (delimiter, header, ambiguous dates) for dataset 85. |
| `dataset.file-settings.update` | ok | Confirmed file settings; dataset transitioned to status=ready with dataview 106 created (job id 584). |
| `view.list` | ok | Listed 1 dataview: id=106, ds_id=85, status=ready, row_count=3. Note: response includes a 'next' pagination URL (offset=100) despite only 1 total item, possibly a minor pagination defect. |
| `webhook.create` | ok | Created webhook id=1, which auto-created a backing dataset ds_id=86. |
| `webhook.list` | ok | Listed webhooks, showed id=1 correctly. |
| `webhook.get` | ok | Fetched webhook 1, fields match create response. |
| `webhook.update` | ok | Updated mode replace->combine; response reflects new mode. |
| `webhook.delete` | ok | Deleted webhook 1; read-back list is empty, confirming deletion. |
| `schedule.create` | backend_error | Backend returned 5GENR011 NOT_IMPLEMENTED for bare-rrule schedule create. |
| `schedule.create` | backend_error | Second create attempt (with work_items bound to dataset 85) returned HTTP 500 with empty response body, surfaced by CLI as code=outcome_unknown. Immediately following schedule.list also 400 NOT_IMPLEMENTED, confirming the feature is unimplemented on this release backend. |
| `schedule.list` | backend_error | Backend 5GENR011 NOT_IMPLEMENTED confirms schedule feature is entirely unavailable on this release backend; skipped schedule.get/update/delete per brief. |
| `automation.create` | ok | Created automation id=1 after two failed attempts: agent_example's run_data_retrieval needs cloud-source dataset ids (4AUTO006), and send_an_alert needed attachments.dataview_ids (undocumented shape) in addition to recipients/subject. |
| `automation.get` | backend_error | automation.get on the id that automation.create returned (id=1) returns HTTP 500 empty body every time (3 retries, several seconds apart). |
| `automation.list` | ok_empty | list never shows automation id=1 even though create returned it with status=active; repeated after delays, still empty data:[]. |
| `automation.update` | cli_error | CLI rejected 'name' field; error message says accepted field is 'patch' (nested patch object), not documented in agent_example. |
| `automation.delete` | ok | Delete returned 200/data:{} despite get/list never having shown the resource; cannot independently confirm deletion given get/list breakage for this id. |
| `workflow.create` | ok | Created workflow id=1 seeded from dataset 85. |
| `workflow.get` | ok | Read back workflow 1, fields match create response. |
| `workflow.update` | ok | Updated notes field; response reflects change and bumped updated_at. |
| `workflow.delete` | ok | Deleted workflow 1; read-back get now returns 404 WORKFLOW_NOT_FOUND, confirming deletion. |
| `snippet.create` | ok | First attempt with hyphenated name 'sweep-218 snippet' failed 4SNPT006 (name must be letters/digits/underscore); retried with sweep_218_snippet, created id=1 scope=project. |
| `snippet.list` | ok | Listed snippets, total_count=1 showing id=1. |
| `snippet.get` | ok | Fetched snippet 1 with dependencies/history fields added. Minor note: meta.project_id is null here (and on dependencies/update/delete) while list/create show 41. |
| `snippet.dependencies` | ok_empty | No dependencies for unused snippet, as expected. |
| `snippet.update` | ok | Updated description; response reflects change. |
| `snippet.delete` | ok | Deleted snippet 1; read-back list shows total_count=0. |
| `template.create` | ok | Created template id=1 status=draft (workspace-scoped, no dataset/view source needed since template_data is optional). |
| `template.list` | ok | Listed templates, showed id=1 only. |
| `template.get` | ok | Fetched template 1, matches create. |
| `template.update` | ok | Updated description field. |
| `template.delete` | ok | Deleted template 1; read-back list is empty. |
| `parameter.create` | ok | First attempt with lowercase param_type 'text' failed 4PARM008 (must be NUMERIC/TEXT/DATE, uppercase; schema example is misleadingly lowercase). Retried with TEXT, created id=1. |
| `parameter.list` | ok | Listed parameters, total_count=1 showing id=1. |
| `parameter.get` | ok | Fetched parameter 1 with dependencies/history fields. |
| `parameter.dependencies` | ok_empty | No dependencies, as expected. |
| `parameter.update` | ok | Updated value hello->world. |
| `parameter.delete` | ok | Deleted parameter 1; read-back list shows total_count=0. |
| `external-key.list` | ok_empty | No owned external_keys present; one house_key (open_ai, in_use) visible read-only, not touched. |
| `external-key.create` | blocked_missing_fixture | Backend validates the key live against the real OpenAI API (4WKSP003, 401 invalid_api_key); no real provider credentials available per task rules, so get/delete skipped (nothing created). |
| `view.checkpoint.create` | ok | First attempt without pinned_to_end/task_sequence failed 4GENR007 (schema's own example omits the requirement). Retried with pinned_to_end:true, created checkpoint id=4. |
| `view.checkpoint.list` | ok | Listed checkpoints, showed id=4. |
| `view.checkpoint.get` | ok | Fetched checkpoint 4, matches create. |
| `view.checkpoint.update` | ok | Sending a full AddCheckpointSpec body failed with invalid_input_field_type; update actually needs body.patches[] (op/path enums approve\|enable\|disable\|spec). Retried with a disable command-patch, succeeded. |
| `view.checkpoint.delete` | ok | Deleted checkpoint 4 (202); read-back list is empty. |
| `view.data-check.create` | ok | Passing explicit threshold:5.0 (matching the schema's own documented type/default) caused invalid_input_field_type. Omitting threshold succeeded, created data_check_id=4. |
| `view.data-check.get` | ok | Fetched data check 4, threshold shows as 0 (applied default). |
| `view.data-check.update` | backend_error | PATCH returned HTTP 500 empty body / outcome_unknown, but a follow-up get confirmed the mutation actually applied (enabled:false). Server-side success, 500 response envelope. |
| `view.data-check.delete` | ok | Deleted data check 4 (202); read-back get returns 404, confirming deletion. |
| `view.derivative.create` | ok | Created a SUM(amount) metric derivative on view 106, id=5. |
| `view.derivative.data` | backend_error | Using the CLI's own documented agent_example body verbatim, derivative data fetch returns HTTP 500 empty body / outcome_unknown, reproduced twice. Read-only fetch, not a mutation. |
| `view.derivative.delete` | ok | Deleted derivative 5 (202). |
| `file.upload` | cli_error | file.upload with append_to_ds_id set raises a raw client-side ValueError (~100ms, no HTTP call logged), in both positional+--input and --input-only forms. |
| `file.upload` | ok | Uploaded fixture2.csv as new dataset_id=87, used purely as a batch-create source fixture. |
| `dataset.file-settings.update` | ok | Confirmed settings for dataset 87; reached status=ready. |
| `batch.create` | backend_error | First attempt used source_id=87 as the original file-source id (from dataset.get sources[].details.id) and got 4BATC010 INVALID_SOURCE_DATASET - the actual expected 'source_id' is another dataset id. |
| `batch.create` | backend_error | Retried with source_id=87 as an actual dataset id; got HTTP 500 empty body / outcome_unknown. Verified via batch.list that the batch was NOT created — genuinely failed, not silently applied. |
| `batch.list` | ok | Listed the auto-created batch (id=90) from the original file upload; confirmed the failed batch.create above added nothing. |
| `batch.get` | ok | Fetched batch 90 detail, matches list. |
| `batch.delete` | ok | Deleted batch 90 (async job_id=612); read-back batch.list confirms 0 active batches. |
| `view.exportable-config.get` | ok | Fetched full exportable config for view 106. |
| `view.exportable-config.apply` | cli_error | The command's own agent_example ({"config": {"tasks": []}}) fails - async job errors needing 'dependencies', then 'metadata'. Only the FULL get() payload resubmitted verbatim worked. |
| `view.exportable-config.apply` | ok | Re-applied the view's own exportable config verbatim (idempotent no-op); returned dataview_id=106. |
| `view.task.preview` | ok | Previewed a COPY task using the documented agent_example shape; metadata correctly shows new column_9. data:[] came back empty despite 3 source rows (may be expected preview behavior). |
| `dataset.bulk-update` | skipped_out_of_scope | schema precondition says 'BLOCKED[B07 DATASET_PATCH_UNTYPED]; reserved, not registered'; live backend wants a JSON-Patch body (patch.op/path/value) that the documented patch_data field doesn't match (4GENR007). Project-wide high-impact op; stopped here per the brief's fail-closed treatment for dataset/view update. |
| `template.list` | ok_empty | Re-check after cleanup: empty. |
| `webhook.list` | ok_empty | Re-check after cleanup: empty. |
| `browse.root` | backend_error | GET /browse returns HTTP 500 empty body, reproduced twice. Read-only, no fixture needed. |
| `browse.project` | backend_error | GET .../projects/41/browse also 500s empty body, same pattern as browse.root. |
| `browse.workspace` | ok | Works fine and lists workspace resources — contrasts with browse.root/browse.project both 500ing. |
| `connector.list` | ok | Listed 42 available connectors. |
| `connector.get` | backend_error | Rejects the exact name_key values returned by connector.list ('azure_blob', 'bigquery') with 4CNTR002 INVALID_CONNECTOR_KEY. |
| `workflow.list` | ok_empty | Empty after cleanup, as expected. |
| `notification.list` | ok_empty | No notifications. |
| `activity.list` | ok | Returned activity_logs scoped to project 41. |
| `report.list` | ok_empty | No reports. |
| `user.list` | cli_error | Brief's route name 'user list' does not exist (usage_error); the actual command is 'user get'. Not a CLI defect, a brief/route naming mismatch. |
| `user.get` | ok | Returned current user's profile. |
| `workspace.get` | ok | Returned workspace 4 profile. |
| `connector.ai.session.list` | ok_empty | No AI chat sessions for connectors. |
| `parameter.list` | ok_empty | Empty after cleanup. |
| `snippet.list` | ok_empty | Empty after cleanup. |
| `schedule.list` | backend_error | Re-confirms 5GENR011 NOT_IMPLEMENTED. |
| `automation.list` | ok_empty | Empty (consistent with earlier observation that created automations never surface in list). |
| `dataset.delete` | ok | Deleted dataset 87 (fixture2.csv). |
| `dataset.delete` | ok | Deleted dataset 86 (webhook-backing dataset). |
| `dataset.delete` | ok | Deleted dataset 85 (main fixture.csv/view 106). |
| `dataset.list` | ok_empty | Confirmed all 3 owned datasets gone before deleting the project. |
| `project.delete` | ok | Deleted project 41, read back with project get 41 beforehand. |
| `project.list` | ok | Final check: only project 3 (pre-existing, not touched) remains; project 41 is gone. |

(Full machine-readable log with argv/exit/http_status for every call: `results.jsonl`, 91 records.)

## Created ids and cleanup proof

| resource | id | created via | deleted via | proof of deletion |
|---|---|---|---|---|
| project | 41 | `project create` | `project delete 41 --yes --confirm 41` (202) | `project list` final call shows only pre-existing project 3 |
| dataset | 85 (fixture.csv) | `file upload` + `file-settings update` | `dataset delete 85 --yes` | `dataset list` empty before project delete |
| dataset | 86 (webhook-backing) | auto-created by `webhook create` | `dataset delete 86 --yes` | same |
| dataset | 87 (fixture2.csv) | `file upload` | `dataset delete 87 --yes` | same |
| dataview | 106 | auto-created on dataset 85 ready | deleted with dataset 85 | — |
| webhook | 1 | `webhook create` | `webhook delete 1 --yes` | `webhook list` → `[]` |
| automation | 1 | `automation create` | `automation delete 1 --yes` | could not independently confirm (automation.get/list broken for this resource even right after create — see defects) |
| workflow | 1 | `workflow create` | `workflow delete 1 --yes` | `workflow get 1` → 404 WORKFLOW_NOT_FOUND |
| snippet | 1 | `snippet create` | `snippet delete 1 --yes` | `snippet list` → total_count=0 |
| template | 1 | `template create` | `template delete 1 --yes` | `template list` → `[]` |
| parameter | 1 | `parameter create` | `parameter delete 1 --yes` | `parameter list` → total_count=0 |
| view checkpoint | 4 | `view checkpoint create` | `view checkpoint delete` (202) | `view checkpoint list` → `[]` |
| view data-check | 4 | `view data-check create` | `view data-check delete` (202) | `view data-check get` → 404 |
| view derivative | 5 | `view derivative create` | `view derivative delete` (202) | (dataset deleted; derivative deleted first) |
| batch | 90 (auto from upload) | implicit on file upload | `batch delete 85 90 --yes` (job 612) | `batch list 85` → 0 active batches |

No external-key, schedule, or dataset-bulk-update resource was ever created (all three families failed
before any mutation committed — see defects below).

## Suspected CLI/backend defects

1. **`schedule.create`** — 5GENR011 `NOT_IMPLEMENTED` on the plain-rrule form (400); a second attempt
   with `work_items: [pull_cloud_data]` bound to our dataset instead returned an empty-body **HTTP 500**
   surfaced as `outcome_unknown` (exit 7). `schedule.list` also 400s with the same NOT_IMPLEMENTED code —
   the whole schedule feature appears unwired on this release backend.
2. **`automation.get` / `automation.list`** — `automation.create` returns a normal 200 with `id=1,
   status=active`, but `automation.get 1` immediately and repeatedly (3x, several seconds apart) returns
   an empty-body **HTTP 500**, and `automation.list` never shows the automation at all (`data: []`). The
   resource is unreadable via both its accessors from the moment it's created.
3. **`automation.update`** — CLI rejects a `name` field with `unknown_input_field`; the schema's only
   accepted field is `patch` (undocumented in the `automation update` agent_example).
4. **`view.data-check.update`** — a `PATCH .../data-checks/4` call returns empty-body **HTTP 500**
   (`outcome_unknown`), but a follow-up `get` shows the mutation *did* apply server-side (`enabled: false`).
   The write succeeds; the response envelope is a 500.
5. **`view.derivative.data`** — using the CLI's own documented `agent_example` body verbatim
   (`{"body": {"condition": {"FILTER_TYPE": "SHOW"}}}`) against a derivative this run created returns
   empty-body **HTTP 500** / `outcome_unknown`, reproduced twice. This is a read, not a mutation.
6. **`batch.create`** — same empty-body **HTTP 500** / `outcome_unknown` pattern, confirmed via
   `batch.list` immediately after that nothing was actually created. Also: the schema/agent_example calls
   the second positional `SOURCE_ID`, but it must be another **dataset id**, not the file-source id
   returned in `dataset.get().sources[].details.id` (400 `4BATC010 INVALID_SOURCE_DATASET` if you use the
   latter) — undocumented and error-prone.
7. **`file.upload` with `append_to_ds_id`** — raises a raw client-side `ValueError` in ~100ms with no
   HTTP call logged and no message beyond `exception_type: ValueError`, both when combined with a
   positional file path and when passed entirely via `--input`. Blocks the append-to-existing-dataset
   upload path entirely.
8. **`connector.get`** — rejects the exact `name_key` values returned by `connector.list` (tried
   `azure_blob` and `bigquery`) with `4CNTR002 INVALID_CONNECTOR_KEY` (400). List and get disagree on
   what a valid connector key is.
9. **`browse.root` / `browse.project`** — both return empty-body **HTTP 500**, reproduced, while
   `browse.workspace` (same underlying data, wider scope) works fine. Read-only, no fixture required.
10. **`view.checkpoint.create` / `view.data-check.create`** — both commands' own documented
    `input_schema` examples don't work as-is: checkpoint create needs `pinned_to_end` or `task_sequence`
    set even though the example omits both (400 `4GENR007`); data-check create rejects an explicit
    numeric `threshold` value that matches its own declared type (`invalid_input_field_type`), only
    working if the field is omitted entirely.
11. **`view.checkpoint.update`** — the schema's rendered example implies you resend the same shape as
    `create` (an `AddCheckpointSpec`), but the endpoint actually requires a `CheckpointPatches`
    (`{"patches": [{"op": "command", "path": "disable", ...}]}`) envelope; sending the create-shaped body
    fails with `invalid_input_field_type`.
12. **`view.exportable-config.apply`** — the command's own `agent_example`
    (`{"config": {"tasks": []}}`) fails an async job twice in a row with `KeyError`-shaped reasons
    (`'dependencies'`, then `'metadata'`); only resubmitting the *entire* object returned by
    `exportable-config get` verbatim succeeds. The minimal documented example is not usable in practice.
13. **`dataset.bulk-update`** — `schema get` marks this command's precondition
    `BLOCKED[B07 DATASET_PATCH_UNTYPED]; reserved, not registered`, and its only documented field
    (`patch_data`, an arbitrary object) does not match what the live backend actually validates
    (`patch.op` / `patch.path` / `patch.value`, JSON-Patch style) — confirmed via a live 400
    `4GENR007 VALIDATION_ERROR`. Left unexercised beyond this probe per the brief's fail-closed guidance,
    since it is a project-wide high-impact op with an internally-flagged-reserved contract.

### Recurring pattern worth flagging structurally
Four independent commands (`schedule.create` w/ work_items, `view.data-check.update`,
`view.derivative.data`, `batch.create`) all produced an **empty-body HTTP 500** that the CLI reports as
`code=outcome_unknown, retryable=false, exit=7` with the instruction "Do not replay this operation." In
two of these cases we were able to verify via a follow-up read that the underlying mutation had actually
committed (data-check.update) or had definitely not committed (batch.create) — the CLI itself cannot tell
these apart from the response it receives, which is a real reliability gap for anything scripting around
`outcome_unknown`.

## Non-defect notes (brief/route mismatches, not CLI bugs)
- Brief's route #17 lists `user list`; the actual command tree only has `user get` (no list subcommand).
- The schema examples for `automation.create` (run_data_retrieval) and `send_an_alert` require
  fields (`ds_details` pointing at cloud datasets; `attachments.dataview_ids`) not shown in the rendered
  `agent_example` — worked around empirically.

## Timing
Sweep completed in ~30 minutes of a 60-minute budget; stopped attempting new families well before the
50-minute mark, all cleanup done and verified.
