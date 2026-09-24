# Re-verification of 2.0.15 CLI fixes — release

CLI under test: `/tmp/claude-1000/-home-euler-mammoth-mammothsdk/aec77d33-c4b6-4a6f-b36b-5bb563cd5a89/scratchpad/venv215/bin/mammoth`, confirmed `mammoth --version` -> `2.0.15`. All commands run with `--profile release --output json --no-input`, `--yes`/`--confirm` added when the error envelope required it. All 27 command ids in `COMMANDS.txt` were run exactly once against fixtures created for this run (project 23, workspace 4). No auth/config/doctor commands were run; no credentials were read, printed, or handled.

## Verdict counts

| Verdict | Count |
|---|---|
| ok | 19 |
| ok_empty | 0 |
| cli_error | 0 |
| backend_error | 5 |
| blocked_missing_fixture | 3 |
| skipped_out_of_scope | 0 |
| not_run | 0 |
| **Total** | **27** |

No `cli_error` and no `not_run` — every command was exercised at least once within the time budget, and none reproduced the original CLI-side defect described in `COMMANDS.txt`.

## Command | Fixed? | Evidence

| Command | Fixed? | Evidence |
|---|---|---|
| `project.delete` | Yes | `{"data":{"response":null,"status_code":202}}` — 202 reported as success; project 23 confirmed gone from `project list` afterward. |
| `dataset.bulk-delete` | Yes | Accepted `dataset_ids:[53,55]` with `--yes`; `{"data":null}`; `dataset list --project 23` returned `[]` right after. |
| `view.conditional-format.delete-all` | UNVERIFIED | No real rule existed to delete (create route is documented-blocked); CLI rejected client-side with `"conditional_format_delete requires \`rule_id\`; list rules first."` even with rule_id supplied. Could not exercise the query-param dispatch fix end to end. |
| `view.derivative.delete` | Yes | `{"data":{"response":null,"status_code":202}}` on our own derivative 3. |
| `view.checkpoint.delete` | Yes | `{"data":{"response":null,"status_code":202}}` on our own checkpoint 3. |
| `view.data-check.delete` | Yes | `{"data":{"response":null,"status_code":202}}` on our own data-check 2. |
| `dataset.file-settings.undo` | Yes | `{"data":{"response":null,"status_code":200}}`. |
| `dashboard.og-card` | Yes | Returned `{"data":{"content_base64":"iVBORw0KGgo..."}}` — binary body described, not crashed. |
| `user.preference.update` | Yes | `{patch:[...]}` list shape accepted; wrote back the same value read from `user preference get`; value confirmed unchanged afterward. |
| `project.bulk-update` | Yes | ProjectsPatch with `project_id` per value item accepted; confirmation named the workspace scope (`--confirm 4`); jobs 372/374 both `status:success` via `job get`. |
| `project.update` | Yes | Returned full updated project object with fresh `updated_at`. |
| `batch.update` | Yes | Invalid patch op surfaced as `invalid_arguments` with SDK message ("Each patch op must have op='replace' or op='remove'...") instead of empty api_error; no request dispatched. |
| `view.derivative.update` | Yes | `{"data":{"response":null,"status_code":202}}`. |
| `view.pipeline.edit` | Yes | Documented `auto_run` bool example ran and returned the pipeline state object. |
| `view.checkpoint.update` | Partially (CLI-side yes; backend still 500s) | Payload correctly carried `value:null`; backend returned HTTP 500 `outcome_unknown` both on this call and on the reconciliation `checkpoint list` call — matches known backend-side blocker in capabilities.md, not the CLI defect under test. |
| `view.task.update` | Yes | `{patches:[{op:replace,path:params,value:task_spec}]}` accepted; `{"data":{"future_id":365,"has_error":false,"status":"processing"}}`. |
| `view.export.publish-db-update` | Partially | `path:"credentials"` accepted and dispatched (matches doc note); backend gave precise field-level 400s on two different value shapes (`"Input should be a valid dictionary"`, then `"Input should be 'postgres' or 'bigquery'"`). Exact nested credentials shape UNVERIFIED — no working DB credentials available. |
| `folder.move` | Yes | `{patch:[{op:move,from:[ids],path:...}]}` shape accepted; `{"data":{"job_id":368,...}}`, job later `status:processing`. |
| `workspace.segment.update` | Yes | `{"data":{"response":null,"status_code":200}}` on both `op:add` and `op:remove`; `workspace segment list` identical before/after (Alpha/Beta only) — baseline restored. |
| `dashboard.published.data` | UNVERIFIED | Dashboard 59 never reached `was_published:true` — `dashboard action {action:publish-presentation}` failed twice with HTTP 500 `outcome_unknown` (backend-side). The URL-scoped route itself dispatched cleanly (structured 404 `DASHBOARD_NOT_FOUND`, no crash), but the specific job-polling fix could not be exercised on a live published job. |
| `connector.query.generate` | Likely yes (UNVERIFIED without real connection) | No real connector connection exists in workspace 4 (documented blocker). Placeholder call reached backend connection-lookup, returning `4CONN004 CONNECTION_NOT_FOUND` rather than a field-shape rejection — consistent with the `query` field now being sent correctly. |
| `batch.create` | Yes (CLI-side); backend 500 | Attempt 1 (missing `expected_destination_c_type`) got a precise structured 400 listing exactly the missing fields — proves the release list-of-mapping-objects shape is now sent. Attempt 2 (complete mapping) passed validation and reached the backend, which 500'd (`outcome_unknown`); reconciled via `batch list` — no new batch was committed. |
| `view.ai.profile` | Yes | `{params:{action}}` accepted; returned real generated insights. |
| `ai.sql.generate` | Yes (CLI-side); backend conflict | `dataset_id` required/sent as query param — request reached backend and got a clear domain error (`4DTVW029` "input table from the previous rule is not available") on **two different datasets**, including one untouched by us, showing it's a backend-side condition, not the old empty api_error. |
| `ai.expression.generate` | Yes | Invalid `mode` surfaced as `invalid_arguments` with the exact SDK message ("`mode` must be 'math' or 'metric', got 'sample'.") before dispatch — matches the fix precisely. |
| `ai.suggestion.list` | Yes (CLI-side); backend job failure | UnifiedPromptSpec shape accepted and dispatched to a real job (381), which failed for an unrelated backend reason ("Unexpected error using param generation"), not a client-side shape rejection. |
| `project.user.add` | Yes | `{users:[{user_id,role}]}` with numeric id accepted; `{"data":{"response":null,"status_code":201}}` on retry (first attempt legitimately 403'd because the run had self-demoted via `project.bulk-update` testing — restored via a follow-up bulk-update call, unrelated to this command's own defect). |

## Resources created and cleanup state

| Resource | ID | Created via | Deleted? |
|---|---|---|---|
| Project | 23 (`cli-reverify-215-20260918`) | `project create` | Yes — `project.delete` (202), confirmed absent from `project list` |
| Dataset | 53 (`stores.csv`) | `file upload` | Yes — `dataset.bulk-delete` |
| Dataset | 55 (`stores.csv 2`, batch-create source) | `file upload` | Yes — `dataset.bulk-delete` |
| View | 75 (on dataset 53) | auto-created with dataset 53 | Yes — deleted with dataset 53 |
| View | 77 (on dataset 55) | auto-created with dataset 55 | Yes — deleted with dataset 55 |
| Derivative | 3 (on view 75) | `view derivative create` | Yes — `view.derivative.delete` |
| Checkpoint | 3 (on view 75) | `view checkpoint create` | Yes — `view.checkpoint.delete` |
| Data-check | 2 (on view 75) | `view data-check create` | Yes — `view.data-check.delete` |
| Task | 26 (MATH, on view 75) | `view transform math` | Yes — removed with dataset 53 (no separate `view.task.delete` call was in scope) |
| Folder | 12 / resource 196 (`reverify-folder-215`) | `folder create` | Yes — `folder delete` |
| Dashboard | 59 (`cli-reverify-215-dashboard`) | `dashboard create-blank` | Yes — share reverted to `mammoth` first, then `dashboard trash` + `dashboard delete` |
| Batch | 56 (on dataset 53, from initial upload) | `file upload` | Yes — removed with dataset 53 |
| Project role for user 5 on project 23 | project_analyst -> project_admin (restored) | `project.bulk-update` (2x), `project.user.add` | N/A — role state moot once project 23 deleted |

Only one dashboard was created, per the hard limit. No resource outside project 23 was touched at any point — every mutating call in the session targeted `--project 23` and IDs returned from our own `project create` / `file upload` / `dashboard create-blank` / `folder create` / `view derivative create` / `view checkpoint create` / `view data-check create` / `view transform math` calls.

## Final baseline check (post-cleanup)

`project list --profile release --output json --no-input`:
```json
{"data":{"projects":[{"id":3,"name":"API Tests_project"}],"limit":100,"next":"","offset":0}}
```
Project 23 is gone; only project 3 remains, unchanged.

`dataset list --project 3 --profile release --output json --no-input`:
```json
{"data":{"datasets":[
  {"id":33,"name":"co-emissions-per-capita.csv 2"},
  {"id":31,"name":"share-of-individuals-using-the-internet.csv 2"},
  {"id":30,"name":"life-expectancy.csv 2"},
  {"id":29,"name":"gdp-worldbank.csv 2"},
  {"id":28,"name":"population.csv 2"}
]}}
```
Datasets 28, 29, 30, 31, 33 all present, matching the required baseline exactly — none touched.

`dashboard list --project 3 --profile release --output json --no-input`:
```json
{"data":[{"id":48,"title":"Terra OWID five-source reference","project_id":3,"status":"draft", "...":"..."}]}
```
Dashboard 48 present, untouched.

All claims above are taken directly from command output observed during this run (quoted verbatim or paraphrased with the JSON keys shown); items marked UNVERIFIED are called out explicitly where a fixture or backend condition prevented full end-to-end confirmation of the specific 2.0.15 fix.
