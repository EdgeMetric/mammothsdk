# CLI write sweep — release, CLI 2.0.14

79/79 command ids from `COMMANDS.txt` run (or deliberately not run, with reason) against a disposable fixture in workspace 4. Results are in `results.jsonl`, one line per command id.

## Verdict counts

| Verdict | Count |
|---|---|
| ok | 32 |
| ok_empty | 5 |
| cli_error | 29 |
| backend_error | 8 |
| blocked_missing_fixture | 2 |
| skipped_out_of_scope | 3 |
| **total** | **79** |

## Fixtures created

- Project **21** `cli-write-sweep-20260918` (main fixture) — dataset **48** (`stores.csv`, view **68**), plus datasets **49**, **51**, **52** (sample-flow), views **72**, **73**, **74**, folders **7**, **8**, checkpoint 1, data-check 1, derivative 2, exports 2/3, task 24, pipeline versions 29-41 — all created during the sweep and never overlapping project 3.
- Project **22** `cli-write-sweep-throwaway-20260918` — created solely to exercise `project.bulk-delete`.
- Scratch files in this directory: `sample.pdf` (synthetic, for `dataset.create-from-pdf`), `exported_stores.csv`, `append.py` (jsonl writer helper) — local only, not remote resources.

## Cleanup

- Project **22**: deleted via `project.bulk-delete` — verified gone from `project list`.
- Project **21** (and everything inside it — datasets 48/49/51/52, views 68/72/73/74, folders, checkpoints, data checks, derivatives, exports, tasks, versions): deleted via `project.delete`. CLI reported `outcome_unknown` (HTTP 202 misclassified — see below) but `project list` afterward shows only project 3, and `dataset list --project 21` now returns HTTP 403 `authorization_required` (project no longer accessible) — deletion confirmed by observed command output.
- No datasets/views/folders/projects created by this sweep remain.

## Non-ok commands (verdict | error)

- **ai.expression.generate** | cli_error — both `mode:sample` and `mode:generate` return an identical opaque `api_error` with no HTTP status or detail.
- **ai.retention.condition** | backend_error — HTTP 403 `4PERM001 PERMISSION_UNDEFINED`: "Permissions have not been set correctly for this API, please contact Mammoth Help to report this error."
- **ai.sql.generate** | cli_error — runnable_example omits `dataset_id`; backend requires it (HTTP 400 `4GENR007`), and the CLI schema has no field to supply it (`unknown_input_field`).
- **ai.suggestion.list** | cli_error — CLI sends an empty POST body; backend wants a `data` field it never provides (HTTP 400 `4GENR007`).
- **batch.create** | cli_error — CLI types `mapping` as an object; backend requires a list of `ColumnNameMapping`/`ColumnIdMapping` objects (HTTP 400 `4GENR007`), and the CLI rejects a list client-side.
- **batch.update** | cli_error — both plausible patch shapes (`id`/`batch_id`) return an identical opaque `api_error`.
- **connector.query.generate** | cli_error — CLI only accepts `prompt`; backend requires `query` (HTTP 400 `4GENR007`), rejected client-side when added.
- **connector.query.status** | blocked_missing_fixture — no real connector connection exists in workspace 4 (none `is_added`); creating one needs external credentials, out of scope.
- **dataset.bulk-update** | cli_error — matches documented `BLOCKED[B07 DATASET_PATCH_UNTYPED]`; even after discovering the real `patch:{op,path,value}` JSON-Patch shape live, `path` must be the literal string `name` and `value` a dict, none of which the CLI schema hints at.
- **dataset.create-from-pdf** | backend_error — HTTP 400 `4DSET053`/`4DTSTO003`; used a synthetic PDF (no real tabular PDF fixture available), so this may only reflect no real table in the input.
- **dataset.file-settings.undo** | cli_error — backend returns HTTP 200 but CLI reports `outcome_unknown`; a follow-up read then 500s.
- **dataset.update** | skipped_out_of_scope — intentional guardrail (`unsupported_contract B07`), CLI refuses client-side with typed alternatives suggested. Working as designed.
- **file.update** | backend_error — job accepted then stuck in `processing` forever (polled twice over 20s); CLI correctly reported timeout rather than a false success.
- **folder.move** | cli_error — CLI sends `resource_ids`/`target_folder_resource_id` directly; backend requires a `patch` field (HTTP 400 `4GENR007`), rejected client-side when added.
- **project.update** | cli_error — CLI sends `name`/`color` directly; backend requires a `patches` field (HTTP 400 `4GENR007`), rejected client-side when added.
- **project.user.add** | cli_error — CLI sends `user_ids`; backend requires `users` (HTTP 400 `4GENR007`), rejected client-side when added.
- **project.user.remove** | blocked_missing_fixture — `project.user.add` never succeeded, so there was no user we added to remove (per brief, not run against a pre-existing member).
- **project.user.update** | backend_error — HTTP 400 `4PROJ010 ROLE_ALREADY_ASSIGNED` (targeted our own already-admin user; a legitimate no-op rejection, request shape was fine).
- **user.preference.update** | cli_error — CLI sends `theme`/`locale` directly; backend requires a `patch` field (HTTP 400 `4GENR007`).
- **project.bulk-update** | skipped_out_of_scope — **safety finding**: this command has no per-project targeting; its own confirmation message says it would bulk-update ALL projects in workspace 4 (`--confirm 4`), which includes protected project 3. Deliberately never confirmed/executed.
- **view.ai.generation-info** | backend_error — HTTP 400 `5GENR011 NOT_IMPLEMENTED` (matches documented known blocker).
- **view.ai.profile** | cli_error — CLI sends empty POST body; backend wants `data`, CLI has no field for it.
- **view.checkpoint.get** | backend_error — HTTP 500, empty body, reproduced twice, immediately after a successful `view.checkpoint.create`.
- **view.checkpoint.update** | cli_error — runnable_example omits required `value`; corrected shape then 500s (`outcome_unknown`).
- **view.checkpoint.delete** | cli_error — HTTP 202 Accepted misreported as `outcome_unknown` (see systemic finding below).
- **view.conditional-format.create** | cli_error — doc claims this is fail-closed client-side; it actually dispatches a real request and 400s twice with undocumented `cf_type`/`payload` shape.
- **view.conditional-format.delete-all** | cli_error — backend requires a `rule_id` query param even for "delete-all"; CLI has no field for it.
- **view.data-check.update** | backend_error — HTTP 500 on the command-patch route (same shape as checkpoint.update).
- **view.data-check.delete** | cli_error — HTTP 202 misreported as `outcome_unknown`; verified actually deleted (404 on readback).
- **view.derivative.data** | backend_error — HTTP 500, empty body.
- **view.derivative.update** | cli_error — HTTP 202 misreported as `outcome_unknown`; verified the update actually applied.
- **view.derivative.delete** | cli_error — HTTP 202 misreported as `outcome_unknown`; verified actually deleted.
- **view.export.create** | cli_error — the natural `csv_file` case fails both attempts with an undocumented `'destination'` KeyError-shaped job error; no field in the schema can supply it. (A working export was obtained separately via the schema's own `postgres` example for downstream get/update/delete tests.)
- **view.export.publish-db-update** | cli_error — runnable_example and a guessed JSON-Patch shape both fail; ran out of attempt budget before finding the real shape (`path` must be the literal `credentials`, `value` must be `postgres`/`bigquery`).
- **view.exportable-config.apply** | cli_error — runnable_example (`config:{tasks:[]}`) fails with a raw `'dependencies'` KeyError job failure; adding `dependencies:{}` then fails with `'metadata'` — an undocumented, apparently long chain of required top-level keys.
- **view.pipeline.edit** | cli_error — runnable_example fails; a guessed patch reveals an undocumented `path` enum (`auto_run`/`run`/`submit-changes`/`reset`/`discard-changes`/`suspend`/`restore`/`discard`/`reorder`) not in the schema.
- **view.task.preview** | cli_error — runnable_example (`COPY:{}`) fails with a vague "Unknown error occurred. Please contact support." wrapping a real `Source column not present` reason; a guessed corrected `COPY` shape fails identically.
- **view.task.update** | cli_error — CLI sends `task_spec` directly; backend requires `patches` (HTTP 400 `4GENR007`).
- **view.update** | skipped_out_of_scope — intentional guardrail (`unsupported_contract B09`), no typed alternative offered even for a plain rename. Working as designed.
- **workspace.segment.update** | cli_error — runnable_example fails; real shape (`op:add/remove`, `path:segments`, `value:<name>`) discovered live, but the successful HTTP 200 was still misreported as `outcome_unknown`. Verified via `workspace segment list` and reverted to baseline (`Alpha.status:false`) immediately — segment `features` were empty throughout so there was no functional/feature-gated impact on project 3.
- **dataset.bulk-delete** | cli_error — CLI's input schema has zero accepted fields, yet the backend requires explicit dataset ids (HTTP 400 `4DSET025`); the command can never succeed as implemented.
- **project.delete** | cli_error — HTTP 202 Accepted misreported as `outcome_unknown`; verified project 21 actually deleted (see Cleanup).

## Systemic patterns (not per-command, worth fixing once)

1. **HTTP 202 Accepted is misclassified as `outcome_unknown`.** Seen on `view.checkpoint.delete`, `view.data-check.delete`, `view.derivative.update`, `view.derivative.delete`, `workspace.segment.update`, `project.delete` — every one of these mutations actually succeeded (verified by re-reading state) but the CLI reported an unconfirmed/failure-shaped exit 7. This is the single highest-value CLI fix found in this sweep.
2. **CLI-side field names don't match the backend's actual PATCH/POST contract** on `folder.move`, `project.update`, `project.user.add`, `user.preference.update`, `dataset.bulk-update`, `view.task.update`, `connector.query.generate`, `ai.sql.generate`, `batch.create` — the accepted_fields/runnable_example is consistently wrong or incomplete, discoverable only by trial and error against the live error envelope.
3. **`project.bulk-update` has no per-project scope** — a real safety hazard if ever run against a multi-project workspace with `--yes --confirm <workspace_id>`.

## Baseline verification (proving project 3 untouched)

`project list`:
```json
{"projects": [{"id": 3, "name": "API Tests_project"}]}
```

`dataset list --project 3`:
```json
{"datasets": [
  {"id": 33, "name": "co-emissions-per-capita.csv 2"},
  {"id": 31, "name": "share-of-individuals-using-the-internet.csv 2"},
  {"id": 30, "name": "life-expectancy.csv 2"},
  {"id": 29, "name": "gdp-worldbank.csv 2"},
  {"id": 28, "name": "population.csv 2"}
]}
```

`dashboard list --project 3`: one dashboard, `id: 48`, `title: "Terra OWID five-source reference"`.

All three match the protected baseline named in the brief (project 3, datasets 28/29/30/31/33, dashboard 48) exactly, both before and after the sweep. No credentials were read, printed, or handled at any point (the one credential-bearing response, from `project.publish-credentials`, arrived with `password` already redacted by the CLI).
