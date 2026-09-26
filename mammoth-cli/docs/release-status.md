# CLI release provenance

## 2.0.49

Three fixes landed together for this release: a read-only aggregate query
surface for `view.data.*` (plus two related fixes found alongside it), a
dataset-export write-confirmation race, and seven usability gaps surfaced by
tier1/tier2 luna eval traces (koyal).

An in-app agent driving the CLI as its only surface had no read-only way to
answer a question like "total spend by channel" and was mutating the user's
pipeline (`view transform pivot`, then `view task delete` to clean up) just to
read a number. Two more defects found alongside it while reviewing the same
`view.data.*` surface.

- **New (SDK, `mammoth-io` 0.7.21; CLI, `mammoth-cli` 2.0.49)**:
  `DataviewsAPI.aggregate(...)` and `view data aggregate` — a read-only PIVOT
  group-by or single METRIC query against `ExecuteVolatileQuery`
  (`POST .../dataviews/{id}/data/query`). It computes and returns an
  aggregated result without adding a task to the view's pipeline or otherwise
  changing it. `mammoth view data aggregate VIEW_ID --input
  '{"group_by": ["Channel"], "aggregations": [{"column": "Spend", "function":
  "SUM", "as_name": "Total Spend"}]}'`; pass `metric` instead of
  `aggregations`/`group_by` for a single value. The bundled guide's goal
  table now steers an agent here instead of `view transform pivot` for a
  read.
- **Fixed**: `view.data.query`'s manifest declared `operation_ids:
  [ExecuteVolatileQuery]`, but its SDK method (`DataviewsAPI.query_data`)
  actually calls `GetDataviewDataPost` (`POST .../dataviews/{id}/data`, no
  `/query`). The two commands' operation ids were swapped; corrected in
  `spec/manifests/openapi-operations.yaml` and
  `spec/manifests/commands/view.yaml`.
- **Removed**: `dashboard.create` (the legacy AI dashboard-generation
  command, backed by `GenerateDashboard`/`POST /dashboards`). Current apiv2
  has no handler for a bare `POST /dashboards`
  (`apiv2/apiv2/mmai/dashboard/controller.py`); every call 404s. It
  historically returned a structured HTTP 409 `4DASH012
  DASHBOARD_LEGACY_CREATION_RETIRED`, which the bundled guide already
  documented as "not supported" without saying the command can never
  succeed on release. Removed the manifest entry, the CLI handler
  (`dashboard_create`), the SDK method (`DashboardsAPI.create`), and their
  tests; `GenerateDashboard` is now `disposition: server_unavailable` in
  `spec/manifests/openapi-operations.yaml` so it stays a reviewed,
  documented operation rather than disappearing silently. Use
  `dashboard create-blank` or `dashboard v3 generate` instead.

Four defects from a tier1 luna trace replay (koyal), all in `view export
dataset` (`target_ds_id` / `save_as_mode APPEND_TO_DS` into an existing
dataset) and its neighbors.

- **Fixed (SDK, `mammoth-io` 0.7.21)**: `View.export.to_dataset` with
  `target_ds_id` set (writing into an existing dataset) returned the id
  immediately after the export job was accepted, without waiting for the
  write to materialize — unlike the new-dataset path, which already polled
  to `EXECUTED`. A read immediately after `to_dataset` could see stale data.
  `mammoth/view.py`'s `_run_internal_dataset_export` now waits for the
  matching `internal_dataset` export trigger to reach `EXECUTED` (or raises
  a typed timeout error) before returning, on both paths.
- **Fixed (CLI, `mammoth-cli` 2.0.49)**: `view export dataset` result now
  reports the target dataset's `rows_after` (and, for `APPEND_TO_DS`,
  `rows_before`), so an agent does not have to guess whether an append
  landed or re-read the dataset separately to check.
- **Fixed (CLI)**: `view export dataset` with `target_ds_id` equal to the
  source view's own dataset now fails fast with `invalid_arguments` before
  the request is sent, instead of writing a view into its own dataset.
- **Fixed (CLI)**: `file upload --input '{"append_to_ds_id": N}'` with no
  files previously reached the SDK and failed as an opaque `api_error`
  ("ValueError"); it now fails as `missing_argument` naming `files`.
- **Fixed (CLI)**: `view create DATASET --input '{"clone_from": VIEW}'` where
  `VIEW` belongs to a different dataset previously reached the backend,
  which accepts it and produces a broken view (no columns; every later data
  read fails). The CLI now checks `clone_from`'s own dataset against the
  target dataset first and fails with `invalid_arguments`.
- **Fixed (guide/discoverability)**: `mammoth schema find "append rows from
  one dataset into another dataset"` matched only `file.upload` (which needs
  a local file), so a cold agent with both sources already in Mammoth could
  conclude row-stacking was impossible. `view.export.dataset` now also
  matches (the query's filler "one" was sinking the match; added to
  `_DISCOVERY_STOPWORDS` alongside the existing "two"). `SKILL.md`'s goal
  table and `references/about-mammoth.md` ("Union or append two views") now
  mention `view export dataset` for stacking a view already in Mammoth, and
  note that an append is a standing pipeline step: re-running the source
  view appends again, it does not run once.

Seven usability gaps found across tier1 luna eval traces (koyal): three
pipeline/discovery blind spots, an over-cap reference file, an undocumented
diff-against-today recipe, an embedded-mode dead end on the CLI's own
`--help` advice, and two search recall gaps.

- **Fixed (CLI + SDK, `mammoth-cli` 2.0.49 / `mammoth-io` 0.7.21)**: a task
  can run and still fail at run time -- a GEN_AI step hitting a workspace AI
  quota, for example -- with the column coming out blank while `has_error`
  stays false and `pipeline_state` reads `ready`. The only signal is the
  task's own `transform_status` (`ERROR`/`REFERROR`), which the server's
  default `__standard` fields mode omits; only `__full` carries it. Root
  cause: `mammoth.api.pipeline.PipelineAPI.get_task`/`list_tasks`
  (`mammoth/api/pipeline.py`) never requested it. Both now always request
  `__full`. `view task add` (`mammoth-cli/mammoth_cli/commands/view.py`,
  `view_ops.reject_task_runtime_error`) also reads the newly added task back
  after the pipeline settles and rejects it with a `task_runtime_error`
  envelope naming the task, its `transform_status`, and the `view task get`
  recovery command, when the run failed without ever flipping `has_error`.
  See `tests/unit/test_api_subclients.py::TestPipelineAPI::test_list_tasks_requests_full_fields`,
  `test_get_task_requests_full_fields`, and
  `mammoth-cli/tests/unit/commands/test_view.py::test_task_add_rejects_a_task_that_failed_at_run_time`.
- **Fixed (guide)**: `references/recipes/transforms.md`'s "verify the write"
  guidance now names `transform_status` explicitly, so an agent reading the
  bundled skill knows a `DONE` step is what "succeeded" actually means.
- **Fixed (CLI)**: the bundled `commands/view.md` and `commands/dashboard.md`
  reference pages exceeded the 65,536-byte agent read cap (71,702 and 69,729
  bytes), so an agent could not read either in one call.
  `scripts/build_skill_catalog.py` now shards an over-cap family by its
  largest `command_id` second segment (`view.transform` ->
  `view-transform.md`, `dashboard.qa` -> `dashboard-qa.md`), peeling the
  largest groups first until the remainder fits, and
  `tests/contract/test_skill_catalog.py::test_every_shipped_reference_file_is_under_the_agent_read_cap`
  guards every shipped reference file going forward.
- **Fixed (guide)**: `view.transform.date-diff`'s manifest entry now
  documents diffing against "today" -- `{"TYPE": "SYSTEM_TIME"}` on either
  operand, sent through the raw `view task add` escape hatch with the
  column's `internal_name` -- verified against the server's task spec
  (`api/api/dataview/helpers/validators/date_diff.py`,
  `CommonConstants/CommonConstants/dba_const.py`'s `__TIME__` wire value).
- **Fixed (CLI)**: `dataset list --input {"project_id": N}` returned a
  generic unknown-field error. `runtime/strict.py`'s
  `_UNKNOWN_FIELD_HINTS` now names the `--project` global option for
  `dataset.list` instead.
- **Fixed (CLI)**: embedded mode (`mammoth_cli.embed.invoke`) discarded
  `--help` output and returned `no_output`, which dead-ended an agent
  following `schema find`'s own no-match hint to run `--help`.
  `embed._run` now captures printed stdout and returns it as a success
  envelope (`data: {"help": ...}`) whenever a call produces no envelope of
  its own.
- **Fixed (CLI)**: `schema get`'s brief mode dropped every field's nested
  JSON Schema, even for non-scalar fields (a union, an object, or an
  array-of-object), forcing an extra `--input {"full": true}` round trip to
  see their keys. `brief_schema` now keeps a field's schema when it is not a
  plain scalar.
- **Fixed (CLI)**: `schema find` had no recall for common math-transform
  phrasings ("calculate ... multiplication", "math conditional formula ...
  threshold") and took multiple searches to reach `view.transform.math`.
  Its discovery purpose text now covers the common phrasings directly.

## 2.0.48

Two defects found from an eval trace and a live task replay on koyal
(mammoth-cli 2.0.47), both in how the CLI treats mutation confirmation and
how its bundled guide teaches combining data.

- **Fixed (CLI, `mammoth-cli` 2.0.48)**: `view export dataset` (and every
  other typed `view.export.*` destination) returned `confirmation_required`
  regardless of the manifest's own `confirmation` field. Root cause:
  `view_export_specialized` (`mammoth_cli/commands/view.py`, the shared
  handler for all 17 typed export routes) passed one hardcoded
  `policy=POLICY_YES_ALWAYS` to `enforce_confirmation` for every route,
  ignoring that the manifest declares `confirmation: none` for
  `view.export.dataset` and `view.export.csv` (no external effect) and
  `confirmation: yes_always` only for routes with one (database, SFTP, BI,
  email, webhook, ...). The in-app agent product decides whether to show a
  confirmation card purely from the manifest, so this runtime-only gate was
  invisible to it and just cost an unconditional extra `--yes`. The handler
  now derives its policy from `command_by_id(invocation.command_id)
  ["confirmation"]`, the same pattern `generated_dashboard` already used for
  the dashboard command family. See
  `mammoth-cli/tests/unit/commands/test_view_export_specialized.py::test_export_route_confirmation_matches_manifest`
  (parametrized over every typed export route) and the tree-wide static
  guard
  `mammoth-cli/tests/contract/test_confirmation_policy_parity.py::test_runtime_confirmation_gate_matches_manifest_for_every_command`.
- **Fixed (guide)**: the bundled skill taught appending/combining two
  sources into one dataset (`file upload --input
  '{"append_to_ds_id": ...}'`, `view export dataset` with `target_ds_id`/
  `save_as_mode APPEND_TO_DS`) but never told the agent to check for rows
  the two sources share. Replaying "combine the east and west orders":
  3 orders present in both source files were counted twice after the
  append, overstating revenue; an earlier run of the same task happened to
  dedupe, so this was variance in agent behavior, not a capability gap.
  `references/about-mammoth.md` ("Union or append two views") and
  `SKILL.md`'s goal table now say to compare the appended view's `row_count`
  against the distinct count of its natural key and run
  `view transform discard-duplicates` (reporting how many rows it removed)
  when they differ.

## 2.0.47

Full live automation lifecycle (`create` → `list` → `get` → `update` rename/
suspend/resume → `delete`, plus `schedule list`) driven through
`mammoth_cli.embed.invoke` on koyal (workspace 4, project 1887
`eval-automation-lifecycle`, deleted after the run), the CLI's actual
in-product-agent entry point. Two defects found and fixed; one previously
documented backend candidate did not reproduce; one backend gap confirmed
unchanged and needs its own design, not a CLI fix.

- **Fixed (CLI, `mammoth-cli` 2.0.47)**: `automation list` with no project in
  context returned the generic `api_error` envelope ("The Mammoth operation
  failed unexpectedly") instead of an actionable error. The in-product agent
  often has no project set. Root cause:
  `AutomationsAPI.list` (`mammoth/api/automations.py` `_proj()`, ~line 308)
  raises a raw `ValueError("project_id must be set on the client using
  client.set_project_id()")`, and `SdkMammothService.call`
  (`mammoth_cli/services/sdk_service.py`) only pre-empted that ValueError for
  three hardcoded `sdk_symbol` strings
  (`PipelineAPI.items_all`, `ViewsResource.delete`, `ViewsResource.get`) —
  every other project-scoped SDK method, including all of `AutomationsAPI`
  (and `FilesAPI`, `WebhooksAPI`, `AIAPI`, `DataviewsAPI`, and 18 more
  `mammoth/api/*.py` call sites sharing the identical message), fell through
  to the generic handler. `call()`'s `except ValueError` branch now matches
  that exact message and raises `missing_project_error()` (code
  `project_required`, recovery `mammoth project list` /
  `mammoth context project use PROJECT_ID`) for any project-scoped method,
  not a hand-kept allowlist; the three-symbol preflight is removed as
  redundant. See
  `mammoth-cli/tests/unit/services/test_sdk_service_project_scope.py::test_every_project_scoped_sdk_method_requires_project_before_transport`.
- **Fixed (SDK, `mammoth-io` 0.7.20)**: `automation update` with
  `path="details"` (rename, description, tasks, or conditions) always
  failed with "must include at least one of: name, description, tasks,
  conditions" even when a field was set — reproduced live for a plain
  rename. Root cause: `AutomationPatchItem.value`
  (`mammoth/models/automations.py`) is typed `str | dict[str, Any] |
  PatchAutomationDetails`; pydantic's default "smart" union mode resolves a
  dict input (what every real caller sends — the CLI's `--input` JSON is
  parsed to a dict before reaching the model) against the exact
  `dict[str, Any]` match rather than coercing it into
  `PatchAutomationDetails`, so `_validate_automation_patch_item`'s
  `isinstance(item.value, PatchAutomationDetails)` check
  (`mammoth/api/automations.py` ~line 236) always failed. The field now
  declares `union_mode="left_to_right"` with `PatchAutomationDetails`
  ordered before `dict[str, Any]`. See
  `tests/unit/test_automations.py::TestUpdate::test_update_details_patch_from_raw_dict_value`.
  Requires `mammoth-io >= 0.7.20`.
- **Not reproduced live (previously documented as a backend candidate in
  2.0.46)**: `automation get AUTOMATION_ID` returning HTTP 500 on an
  automation `automation create` just returned. Live on koyal against
  `feat/agent-cli-surface` (mvc-service commit `8e28a0a594`): two separate
  automations, each read back immediately after creation and three more
  times over 2 s, all returned 200 with the full record — both before and
  after a `status` suspend/resume round trip. The static candidate in
  mvc-service (`apiv2/apiv2/automations/utils.py` `get_automation_tasks()`
  `aut_task = automation_tasks[0]`, unguarded) is still present in that
  commit and remains a real latent defect for an automation whose task
  lookup comes back empty, but the CLI's own create → get lifecycle never
  produces that state (every `automation create` requires at least one
  task), so it is left undisturbed — no live repro, no fix, per this
  project's RCA-before-fix discipline. Re-check if a future sweep finds a
  path that empties an automation's tasks.
- **Confirmed backend limitation, unchanged**: `schedule list` still
  returns HTTP 400 `5GENR011 NOT_IMPLEMENTED` on koyal, matching 2.0.46's
  finding. `apiv2/apiv2/schedules/controller.py`
  `ScheduleController.list_schedules` raises `ClientError` unconditionally;
  its own docstring says the schedule/recurrence tables carry no
  workspace_id or project_id to list by. `ScheduleManager` resolves a
  single schedule's project only indirectly, through
  `validate_and_get_ds(schedule_id, project_id)` (`api/api/scheduler/
  manager.py`) walking to the schedule's `Datasource` and checking its
  `mm_auth_resource_id` against `project_{project_id}` — there is no
  reverse index from project to schedules, so a list would need a new join
  (or a denormalized column) across `ScheduleJob`/recurrence and
  `Datasource`. This is a backend design task, not a simple read; not
  implemented here, per this sweep's own scope.
- **UNVERIFIED**: the mvc-service side of this sweep (both fixed CLI/SDK
  defects) has unit-test coverage only; the live koyal lifecycle run used
  the mammoth-cli 2.0.46 / mammoth-io 0.7.19 build already installed there,
  which is what reproduced the two defects above — it has not yet run
  against a koyal install carrying this release's SDK/CLI fix.

## 2.0.46

Automation/scheduling gap sweep, following up the fixture-lifecycle sweep of
2026-09-19 (`docs/capability-evidence/fixture-sweep-20260919/`).

- **Fixed (CLI/SDK, `mammoth-io` 0.7.19)**: `automation update` with
  `{"patch": [{"op": "replace", "path": "status", "value": "resume"}]}` sent
  `value: "resume"` to the backend verbatim. The backend's wire vocabulary
  for that path is `"suspend"`/`"restore"`
  (mvc-service `apiv2/apiv2/automations/schema.py` `AutomationStatusValueEnum`,
  enforced by `AutomationPatchData.validate_data`), so `"resume"` was
  rejected with `invalid_status_to_update` (400) and a suspended automation
  could never be re-enabled through the CLI. `AutomationsAPI.update` now
  translates its own public `"resume"` value to `"restore"` on the wire; the
  CLI-facing vocabulary (`"suspend"`/`"resume"`, matching `schedule`'s
  `"pause"`/`"resume"`) is unchanged. See
  `tests/unit/test_automations.py::TestUpdate::test_update_status_resume_sends_restore_on_the_wire`.
  Requires `mammoth-io >= 0.7.19`.
- **New test coverage**: `tests/unit/test_automations.py` and
  `tests/unit/test_schedules.py` (29 tests) — the SDK's `AutomationsAPI` and
  `SchedulesAPI` clients had zero direct unit coverage before this release;
  every other case (create with all four task types plus `at_specific_time`
  recurrence, get, list, delete, trash/restore, schedule create/get/update/
  delete) already matched the backend contract and needed no code change.
- **Confirmed backend defect, not fixed here (mvc-service is read-only for
  this repo)**: `automation get AUTOMATION_ID` on an automation
  `automation create` just returned can come back HTTP 500 with an empty
  body, deterministically (three retries, seconds apart — not an
  eventual-consistency race; same finding as the 2026-09-19 sweep).
  Root-caused by reading mvc-service (no live re-run available from this
  environment): the leading candidate is
  `apiv2/apiv2/automations/utils.py` `get_automation_tasks()` line ~778,
  `aut_task = automation_tasks[0]` indexed unconditionally before the loop
  that would otherwise guard it — an unhandled `IndexError` for any
  automation whose task lookup comes back empty matches the empty response
  body (a normal `ClientError` returns a JSON envelope; this does not). A
  second, related candidate in the same handler:
  `apiv2/apiv2/automations/controller.py` `get_automation()` does
  `automations[0]` on `Automation.get_filtered_list(...)` right after
  `Automation.get_by_id()` confirmed the row exists — also unguarded. Full
  trace: `docs/release-capability-matrix.json` `REL-181`. Guide caveat:
  [scheduling recipe](../mammoth_cli/bundled_skill/mammoth-cli/references/recipes/scheduling.md).
- **Confirmed backend limitation, documented (not a bug to fix)**:
  `schedule list` (`GET .../schedules`) is unconditionally unimplemented —
  every call returns HTTP 400, error code `5GENR011 NOT_IMPLEMENTED`
  (`apiv2/apiv2/schedules/controller.py` `ScheduleController.list_schedules`
  always raises `ClientError(not_implemented_error)`; its own docstring
  says the schedule tables carry no workspace/project reference to list
  by). The manifest's `known_restrictions` for `schedule.list` previously
  said "may return 405" — corrected to the confirmed, unconditional 400.
  `schedule create` only ever accepts a `pull_cloud_data` work item
  (`apiv2/apiv2/schedules/helper.py` `ALLOWED_TASK_RESOURCE_MAP`) — this
  already matched the CLI's `WorkItemName` enum, so no CLI change was
  needed; documented explicitly in the new scheduling recipe so an agent
  does not try to fit `run_data_retrieval`/`append_data`/`send_an_alert`/
  `pull_cloud_files` into a `schedule create` body.
- New guide: [recurring work: automations and
  schedules](../mammoth_cli/bundled_skill/mammoth-cli/references/recipes/scheduling.md)
  — the full create/get/update (disable/enable)/delete recipe for both
  resources, with the `automation get` caveat above inline.
- **UNVERIFIED live**: this sweep could not run against koyal (credentials
  unavailable in the environment that did this work — `MMUSER`/`MMPASS` were
  not present at `~/.zshrc` or anywhere else on the box) or reproduce the
  backend defects with a fresh live call (same reason, plus the box's
  locally-installed mvc-service checkout used for a from-source repro
  attempt is a different, unrelated clone with a pre-existing, unrelated
  import-time error). All findings above are from reading mvc-service
  source at `origin/release` and the SDK's own unit tests; the fix is
  covered by a unit test that fails without it, but has not been exercised
  against a live server.

## 2.0.45

From the first live use of the in-product agent (mvc-service, CLI surface).

- `schema find` knows how people ask for recurring work: "schedule a daily
  refresh", "run every week automatically" and "automation refresh dataset"
  now resolve to `automation create`. Before, none matched, the suggestions
  led with `view export dataset`, and the agent concluded there was no
  automation command and used `schedule create` instead.
- The guide's goal table has a scheduling row: `automation create` takes a
  condition (`at_specific_time`, new file in a folder, ...) and tasks
  (`run_data_retrieval`, `append_data`, `send_an_alert`, `pull_cloud_files`);
  `schedule create` only pulls a connector's data; a dataset made from an
  uploaded file has no source to refresh from.

## 2.0.44

For hosts that run commands for their own signed-in users (the Mammoth
in-product agent). No command changes.

- `mammoth_cli.embed.invoke(args, login=..., project_id=..., timeout=...)`
  runs one command in the calling process and returns its success or error
  envelope as a dict. It never raises for a CLI error and writes nothing to
  stdout or stderr. Output is always `json` and prompts are off.
- The login and the result are held in a context variable, so calls in
  different threads do not share them. An embedded call does not read saved
  profiles, does not check for updates and does not write a run log.
- `ExplicitLogin.headers`: extra request headers, set after the credential
  headers so they replace them. A host uses it to send its user's own
  session (`Authorization` and `Cookie`). The endpoint still comes only from
  the server prefix.

Eval `two-files-dashboard`, run through the in-product agent (mvc-service
`AGENT_CLI_SURFACE`, Sonnet 5) on koyal, graded from the persisted transcript:
content checks 2-8 = 7, 7 and one run that stopped at a confirmation card the
eval driver does not answer (2.0.41 baseline: 6, 5, 3). The read-back of the
baked board (`dashboard canvas get`) returned the true revenue in both
finished runs.

CLI published from deterministic local artifacts built from tag `cli-v2.0.44`
(source commit `47d1111`); requires mammoth-io 0.7.18 (unchanged):

- `mammoth_cli-2.0.44-py3-none-any.whl` sha256 `2c1e9b3c1f5fd5c3cddb5192ee0741183a611e7e99c1db1c5faf2cdb226db343`
- `mammoth_cli-2.0.44.tar.gz` sha256 `d0fdbbebffa50f92ab7027936aea17577a6a0557b05acbecde4f9f61b9d4b28c`

## 2.0.43

From the 2.0.41 eval and the release outage the same day.

- `mammoth project check [PROJECT_ID]` (new, read-only): for each dataset,
  the first view's `column_warnings` and `before_dashboard`; for each
  dashboard, its `deliverable_check`; and `to_report`, one line for each
  open finding. The skill tells agents to run it before reporting. Every
  2.0.41 eval run left one column's blanks undecided, because the warning
  was in an earlier result.
- `deliverable_check` adds `columns_not_on_dashboard`: view columns that
  the dashboard's profile lacks (added after the dashboard was made), with
  the `create-blank` command in `fix`. On such a board the money warnings
  are left out, since the fix is the rebuild.
- `doctor --input '{"wait": N}'` (up to 900) probes a failing connection
  again every 15 s while the error is retryable (502, 504, timeout).
- An `outcome_unknown` write with no job handle now names the read that
  settles it: `project get ID` after a project delete, `dashboard list`
  after `create-blank`, `dashboard canvas get ID` after a canvas or pages
  write. On release, agents stalled on these during the outage.

Verified live on release (probe project 101, deleted): `project check`
listed the blanks of both views and `columns_not_on_dashboard` for
`revenue` on a dashboard made before it; `doctor` with `wait` passed.

Backend, not fixed here: the dashboard profile cache key
(`dash3:profile:{dataview_id}:{data_version}`) leaves out the table item,
so a dashboard bound to an older table can store a stale profile for the
current version (see 2.0.41). The fix is to add `table_item_id` to the
key in `dashboards_v3/profile/service.py`.

CLI published from deterministic local artifacts built from tag `cli-v2.0.43`
(source commit `dba1e03`); requires mammoth-io 0.7.18 (unchanged):

- `mammoth_cli-2.0.43-py3-none-any.whl` sha256 `84b8b3d7066b70e1a9bd181c278a85a56a03ecc7eeb2030c16696b7240a998ef`
- `mammoth_cli-2.0.43.tar.gz` sha256 `48f1ad8871b7269191e569630d04ae1241acecb485ae24dc3abb13dbba0301f6`

## 2.0.42

Docs and skill only; no code change. The 2.0.41 agent eval was run three
times on a healthy release backend: 9, 8 and 6 of 10 (mean 7.7; 2.0.40
scored 7). All three runs converted `price` and added `revenue` before the
dashboard step, as the upload's `before_dashboard` said. The two runs whose
dashboards baked both charted revenue. The remaining misses:

- Check 6 (blanks decided) in all three runs: one column's blanks (usually
  `segment`, in the second file) were kept without a word. The report
  checklist now has a row for it: one line for each `blank_values` entry,
  in every view, and kept counts only when it is written down.
- Check 2 (inspect in Mammoth) in two runs: the agent opened the local
  files with `cat`. Step 1 of the multi-file playbook now says not to.
- Checks 7 and 8 in one run: release returned HTTP 500 on `dashboard pages
  add` and `canvas save` (backend).

A first set of three runs was void: release returned 502 and 504 errors
for about 15 minutes. The eval README now says to check release health
first, and to run the three runs one after another, since parallel runs
share the profile's active project (one run uploaded into another run's
project).

CLI published from deterministic local artifacts built from tag `cli-v2.0.42`
(source commit `4bae7e7`); requires mammoth-io 0.7.18 (unchanged):

- `mammoth_cli-2.0.42-py3-none-any.whl` sha256 `4b231873b744b817caaf198a1f53f7a898b85463e57c07d1ab2207552c46b5a5`
- `mammoth_cli-2.0.42.tar.gz` sha256 `428a1a33c5d90ece934ea0ea842731bdedb378507754c2dabae7a06732c53ed8`

## 2.0.41

The 2.0.40 agent eval scored 7 of 10. The agent read the local files, did
not decide on blanks, and charted counts only. The guidance for all three
was in the skill, but the agent did not read that part. This release puts it
in the command output that the agent already reads.

- `file upload` returns a `view` preview for each ready dataset: `view_id`,
  `row_count`, column types, three sample rows, `column_warnings`, and
  `before_dashboard` (the money column to add, with the `math` command in
  `fix`). The view's parent dataset is recorded for later commands.
- `dashboard create-blank`, `canvas save` and `pages add` return
  `deliverable_check`: `money_not_shown` (with the `math` fix when the view
  has a unit price and a quantity), `unit_price_summed`, and `blank_values`
  for each column on the board with blanks. It uses the backend's column
  profile for the canvas. A blank canvas has no profile until its first
  bake, so `create-blank` reads the view instead. Advice only: a failed read
  leaves the result unchanged. Verified live on release.
- A dashboard sees only the columns the view had when the dashboard was
  made. On release, `pages add` refused a `revenue` column added after
  `create-blank` ("isn't a measure in this data"), on that dashboard and on
  a new one made while the old one was still being edited. The backend
  caches the profile under the view and its data version, not the table
  that the dashboard is bound to, so an older dashboard can store a stale
  profile for the current version. A dashboard made after the column, with
  no older dashboard baked in between, charted it. The check's note, the
  upload hint and the skill now say: add the columns first, then make the
  dashboard. (Backend defect; reported, not fixed here.)
- The eval is run three times per release; the result is the mean.

CLI published from deterministic local artifacts built from tag `cli-v2.0.41`
(source commit `88bc42e`); requires mammoth-io 0.7.18 (unchanged):

- `mammoth_cli-2.0.41-py3-none-any.whl` sha256 `ef3733f5ad0a066d1d539091086c636408c7c816578e710cf093a5df6b12fb48`
- `mammoth_cli-2.0.41.tar.gz` sha256 `048e91fc0a40ef7d31e0bbaa6732d09a6c95776de90ca8fe6531344dafd35794`

## 2.0.40 / SDK 0.7.18

The 2.0.39 agent eval scored 8 of 10. The agent charted only `qty` (no
money), did not decide on a blank, and its dashboard kept two empty pages.

- `dashboard pages add` adds `chart_check`. `refused` lists the charts that
  the server refused (for example a `pie` that the data does not support).
  A new page that asked for charts and got none is removed with one canvas
  save and listed in `removed_pages`; `added_page_ids`, `sequence` and
  `bake_job_id` then describe the saved canvas. If the save fails, the
  pages are listed in `empty_pages` with the manual `fix`. Verified live on
  release: the refused page was removed, the other page kept its chart, and
  the bake had no error.
- The dashboards recipe has "Put the money on the board": convert money
  columns to `NUMERIC`, add `revenue` with `math` (`qty * price`) instead
  of summing a unit price, and show it in a KPI and charts.
- The multi-file playbook asks for one report line for each
  `blank_values` entry (column, count, what was done and why).
- `view transform convert-type` skips a conversion to the type the column
  already has, and lists it in `skipped`; when every entry is skipped, no
  task is added (`status: no_change`). On release, converting a NUMERIC
  column to NUMERIC put the pipeline in `ref_error` ("type mismatch"), and
  every read of the view failed until the task was removed. Uploads type
  numbers and ISO dates on their own, so an agent converting "to be safe"
  hit this. Found by the live transform sweep.
- The `pipeline_reference_error` recovery command carries
  `--input '{"dataset_id": N}'`, so it does not fall back to project-wide
  discovery (`/browse`, which returned 502 on release).
- `view transform generate-sql` returns `{sql, applied: false, note,
  apply}`. The route writes and validates a query but adds no task (the
  SDK docstring and the manifest said it did); `apply` is the exact
  `add-sql` command, verified live to give the expected grouped rows.
- SDK 0.7.18 (docs only; behaviour unchanged): `fill_missing` and
  `FillDirection` had the directions reversed. `FIRST_VALUE` is the forward
  fill (previous row's value); `LAST_VALUE` is the back-fill (next row's
  value). `generate_sql` is documented as returning the query without
  changing the view. The CLI skill's fill-missing text is corrected too.

Live sweep (`docs/capability-evidence/transform-sweep-20260925`): all 32
`view transform` commands ran once on release on a synthetic fixture and
were read back against a known answer, 32 of 32. The four findings above
came from it. The capability matrix now lists all 32 as proven.

SDK published from local artifacts built from tag `sdk-v0.7.18` (source
commit `4f82197`):

- `mammoth_io-0.7.18-py3-none-any.whl` sha256 `94f213009dc0bc194ddf0b845713c76a8d7b650c0b026742fe09e7c3194f5e74`
- `mammoth_io-0.7.18.tar.gz` sha256 `a6389ecbadd558fc9116e3aca643af99102b7275fba5de1354d8d9182495d3a7`

CLI published from deterministic local artifacts built from tag `cli-v2.0.40`
(source commit `8cbef87`):

- `mammoth_cli-2.0.40-py3-none-any.whl` sha256 `0d7a697260d3a833ae60efd86549283a2b335f6e39375cf536de97d5b6c3e2b6`
- `mammoth_cli-2.0.40.tar.gz` sha256 `faa2816a1271d26a7efdb12f8843564921ab8f8128780ea7869b509f69b9d1fc`

GitHub release `cli-v2.0.40` (Latest) carries these, both installers and
`SHA256SUMS`; `sdk-v0.7.18` carries the SDK artifacts. Agent eval (Haiku, 2.0.40 from PyPI): 7 of 10 (2.0.39: 8). It
converted `price` from the warning and reported the join (39 of 40,
`C099`), but read the local files first, left the blanks undecided and
charted counts only. The skill's new revenue and blanks guidance was not
reached. Tests: CLI 4500
passed, 2 skipped; SDK unit 1875 passed, 18 skipped.

## 2.0.39 / SDK 0.7.17

A cold agent (Haiku) given "I have two files, t_a and t_b. Create a
dashboard from them" on 2.0.38 found the key and joined, but kept `price` as
text (so the dashboard had no money measure) and left blanks, although it
had seen both. The guide asked for the fix; the CLI output did not.

- `view data get` and `view data query` add `column_warnings`: a text column
  whose values are mostly numbers or dates (with the `convert-type` command
  that fixes it) and blank counts per column. The checks use the rows the
  command already read.
- `view transform join` adds `join_check`: `rows_before`, `rows_after`,
  `columns_added`, `match_rate`, `unmatched_rows`, `unmatched_keys`, and
  notes when rows repeat (a key repeats in the other view) or are dropped.
- `view data get` takes `offset` (1-based) for later pages.
- `dashboard canvas save` with a wrongly nested input names the nesting in
  the error hint.
- The transforms recipe has "What most pipelines look like": defaults drawn
  from an aggregate study of how pipelines are built (short pipelines,
  `new_column` or `existing_column`, `LEFT` joins on one key, key checks
  before a join, `DATE` type before a date step, batched conversions,
  duplicates removed last). The study used counts only; no customer data is
  in the docs.
- The skill tells the agent to act on `column_warnings` and `join_check`,
  to read the uploaded views rather than the local files, and to install
  with `--no-cache-dir` and check the version (a cached index served 2.0.37
  minutes after 2.0.38 was published).
- `evals/two-files-dashboard` holds the scenario, the data and a 10-point
  checklist; RELEASING.md runs it after every CLI release.

CLI published from deterministic local artifacts built from tag `cli-v2.0.39`
(source commit `e22d4cc`; the SDK is unchanged at 0.7.17, so there is no SDK
release):

- `mammoth_cli-2.0.39-py3-none-any.whl` sha256 `114859c2d1da60daa5b58f1e57efee64a23865a027364514635d1b38cdfcf1fd`
- `mammoth_cli-2.0.39.tar.gz` sha256 `acf99f6927a1424bf1653dc5e34835b2d1639e083966001b080fe86e51f52f36`

GitHub release `cli-v2.0.39` (Latest) carries these, both installers and
`SHA256SUMS`. Unit, contract, subprocess and packaging tests: 4494 passed,
2 skipped.

Agent eval (`evals/two-files-dashboard`, Haiku, 2.0.39 from PyPI): 8 of 10
(2.0.38: 7, 2.0.37: 5). It converted `price` from the `column_warnings` fix
and reported the `join_check` match rate (39 of 40, `C099`). Misses: the
`qty` blank was not decided, and the charts used `qty` but no money measure.
Follow-up: `dashboard pages add` keeps a page whose chart was refused, so
the dashboard had two empty pages.

## 2.0.38 / SDK 0.7.17

The CLI had no rename or sort. Both are real web-app actions: a
column-header rename and a grid sort set view display properties
(`COLUMN_NAMES`, `SORT`) through the view PATCH; they add no pipeline task.

- SDK 0.7.17: `View.rename_columns({"old": "new"})` and
  `View.sort_rows([["Col", "DESC"]])`. `View` applies `COLUMN_NAMES` when it
  reads column metadata, so a renamed column (also one renamed in the web
  app) resolves by its new name in later operations.
- CLI: `view transform rename-columns` and `view transform sort`, listed by
  `view transform --help` and found by `schema find "rename column"` and
  `schema find "sort rows by revenue"`.
- The skill has a "Several files, one deliverable" playbook: read every
  view, find the key columns, make them match, fix types and blanks, join,
  then build the dashboard, and say what was inferred.

- The server keeps a view's `metadata` names after a rename. `view get`,
  `view list` and `view data get` now show the renamed column under its new
  name. `view get VIEW_ID --input '{"fields": "__full"}'` without a dataset
  id failed with "unexpected keyword argument 'fields'"; it now returns the
  full record.

Live on release workspace 4 (throwaway project 80, deleted and read back as
not found): upload, `rename-columns` (`cust_ref` to "Customer Ref"), a
`copy-columns` task that names "Customer Ref", `sort` (qty DESC, order_id
ASC), `view get`, `view list`, `view data get` (new name, sorted rows) and
`view export csv` (header "Customer Ref", rows in sort order).

SDK published from local artifacts built from tag `sdk-v0.7.17` (source
commit `fd13f5f`):

- `mammoth_io-0.7.17-py3-none-any.whl` sha256 `607aeb6c655b63b7991e9dcd906c13cad5b5f60d2668518ed438dde3d775e80a`
- `mammoth_io-0.7.17.tar.gz` sha256 `b8c8439c78ad3f238d19fe726e03623d8a5b0c28bd783fa3816c998b342a21da`

CLI published from deterministic local artifacts built from tag `cli-v2.0.38`
(source commit `b5e0ac0`):

- `mammoth_cli-2.0.38-py3-none-any.whl` sha256 `4588f1b2ff2c9eb082bbe9f9930093ab35f1a4fa4837cc6f9c77aa79aace4a97`
- `mammoth_cli-2.0.38.tar.gz` sha256 `98668487cf6920115dbe359b0a3d874f17cce669d2efbbf9dcfbe77ecdddf143`

GitHub release `cli-v2.0.38` (Latest) carries these, both installers and
`SHA256SUMS`; `sdk-v0.7.17` carries the SDK artifacts.

## 2.0.37

An agent that stated a goal in its own words did not find the command. With
2.0.36, `schema find` returned no match for "merge two datasets", "combine
datasets", "vlookup", "dedupe", "rename column", "calculate", "rank" and
"append rows", and "filter rows" returned `ai.suggestion.list` first. An
agent then did a join in the web app, although `view transform join` exists.

- `schema find` knows the common words for all 30 `view transform`
  commands, British spellings, and filler words such as "two" or "my".
  "merge two datasets" returns `view.transform.join` first.
- When no command matches every word, the result adds `suggestions` (the
  commands that match the most words, each with `matched_terms`) and a
  `hint` that names `mammoth view transform --help`.
- The skill has a "What Mammoth is" section, a goal-to-command table, and
  a new reference, `references/about-mammoth.md`: the data model, the
  capabilities, each web Transform-menu task with its command, and the
  nearest route for work that is not a pipeline task (rename, sort, union).
  It tells the agent not to use the web app in a browser for work the CLI
  covers.
- The `AGENTS.md` steering block and the agent prompts say the same.

The SDK is unchanged (0.7.16).

Tests: the full CLI suite passed locally (4461); the doc-example gate now
routes nested `GROUP SUBGROUP --help` examples such as `mammoth view
transform --help`. A clean install of 2.0.37 from PyPI returned
`view.transform.join` for "merge two datasets" and `suggestions` for "union
two views". The live check on release was not run: release.mammoth.io did not
respond (connection timeout) during publication. This release changes no API
call.

CLI published from deterministic local artifacts built from tag `cli-v2.0.37`
(source commit `cce1040`):

- `mammoth_cli-2.0.37-py3-none-any.whl` sha256 `b52921c0e072b75790c9bf17a3a46fd2f713651893b76b1ea961f14b177e7c5a`
- `mammoth_cli-2.0.37.tar.gz` sha256 `88e87557737d7602f58d1ad0648dc29fb1b22cdf004e062f1f05c3d72b8e8278`

GitHub release `cli-v2.0.37` (Latest) carries these, both installers and
`SHA256SUMS`.

## 2.0.36 / SDK 0.7.16

Login uses an API token only. Tokens created in the web app (Workspace
settings → API Tokens) are one `mm_...` value with no secret, and 2.0.35
asked for a key and a secret, so a new token could not log in.

- SDK 0.7.16: `MammothClient(api_token="mm_...", workspace_id=N)` sends
  `Authorization: Bearer`. The `api_key` + `api_secret` pair is deprecated.
- `auth login` asks for the token and the workspace id; `--input` takes
  `api_token`, `workspace_id` and an optional `server_prefix`. A value without
  the `mm_` prefix is refused before any request.
- Profiles saved with a key + secret keep working; `auth status` and `doctor`
  recommend logging in again with a token.
- The 403 hint names project-limited tokens: such a token gets 403 in every
  other project, including one it created.

CI run 35990895848 (Linux 3.12–3.14, macOS, Windows, all installers): tests
green; the docs job failed on one Vale term, fixed in `b7135c0` and verified
locally with the same commands. Live on release workspace 4 with a
project-limited token: login, `auth status --check`, `doctor`, the 403 hint,
and a read in the token's project.

SDK published from local artifacts built from tag `sdk-v0.7.16` (source
commit `8b84a61`):

- `mammoth_io-0.7.16-py3-none-any.whl` sha256 `1ecbdaa6c36c35d811b5f6a3fa1ef9def62c26a780f96829b149e82dda2fdb95`
- `mammoth_io-0.7.16.tar.gz` sha256 `bb0f49ddd35712b27e00378b978a29f293b91efa8d378d65a640c0a2a13b934f`

CLI published from deterministic local artifacts built from tag `cli-v2.0.36`
(source commit `b7135c0`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.36-py3-none-any.whl` sha256 `a24357c0a6c49c9e70e1a54a405caa872e592e719c7cc33d1eef7c326726d0e5`
- `mammoth_cli-2.0.36.tar.gz` sha256 `585ddc07741941b33ca451786ab7c973462c81087573655a2a99e311b4213897`

GitHub release `cli-v2.0.36` (Latest) carries these, both installers and
`SHA256SUMS`; `sdk-v0.7.16` carries the SDK artifacts.

## 2.0.35 / SDK 0.7.15

Two findings from the 2.0.34 cold-start rerun (fresh Sonnet agent, README
prompt only; it installed, stopped for login, upgraded itself 2.0.33 → 2.0.34
and finished the task). SDK unchanged.

- `doctor` now carries `meta.update_available` like every other command
  (only `upgrade` does not), and every envelope reflects a cache refresh the
  command itself made. Before, `doctor` reported a newer release only inside
  its `cli_version` check, so the skill's "if `meta.update_available` is set,
  upgrade" rule never fired on the first command an agent runs.
- `schema get` accepts the command as typed: `'view transform math'` and
  `'mammoth view transform math'` resolve to `view.transform.math`.

Not re-run on CI (pure-Python changes; the 2.0.34 run covered the installers
and macOS). Local: 4411 passed, 2 skipped; ruff, mypy strict, generators
clean.

Published from deterministic local artifacts built from tag `cli-v2.0.35`
(source commit `d381460`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.35-py3-none-any.whl` sha256 `97417551e2150069d1f081515cd9384238da2b48239b1492bd9fd78229d412e5`
- `mammoth_cli-2.0.35.tar.gz` sha256 `7db858b73bdb4ee4c186d2538519f91ea8938fe6f4361de53d1c5feb4c5fb22f`

GitHub release `cli-v2.0.35` (Latest) carries these, both installers and
`SHA256SUMS`.

## 2.0.34 / SDK 0.7.15

Found by a cold-start run: a fresh Sonnet agent given only the README prompt
installed the CLI, stopped for the operator's `auth login`, then uploaded,
computed and read back revenue per region and deleted its project. On that
host uv chose `/usr/local/bin/python3`, a 3.13.0a0 debug build that cannot
load `pydantic_core`, so the installed CLI crashed on import and the
installer blamed the skill install.

- Installers (POSIX and PowerShell) install on a uv-managed CPython first
  and fall back to the system Python when it cannot be downloaded.
- The POSIX installer runs `mammoth --version` after installing and stops
  with the real error and a reinstall command when it fails.
- `mammoth upgrade` passes the interpreter the CLI runs on to uv.
- SDK 0.7.15: math expressions accept a quoted display name
  (`"Unit Price"` or `` `Unit Price` ``); the CLI requires it.

CLI CI ran once before the release (Actions enabled for the run, then
disabled again): run 35978255584, all 11 jobs green, including the
PowerShell installer on Windows.

Published from deterministic local artifacts built from tags `sdk-v0.7.15`
(source commit `3381402`) and `cli-v2.0.34` (source commit `6397db0`). PyPI
reports the uploaded local artifact hashes:

- `mammoth_io-0.7.15-py3-none-any.whl` sha256 `edc11e3125926b658fce9fc579c5d74ff957d03a18e4b2ef76ab36c8fde95a15`
- `mammoth_io-0.7.15.tar.gz` sha256 `100790df05a9296287d19b9b64b671632e12b5cb4ec606be0433467372ea9e69`
- `mammoth_cli-2.0.34-py3-none-any.whl` sha256 `36032443c74dcbf8c974c624d6243b8617cb8524a4d9793cb733b5cb3a6bf20e`
- `mammoth_cli-2.0.34.tar.gz` sha256 `6a718710958f34b3907e820a047573f1998e3eb672b2b625897c13d5eb214390`

GitHub releases `cli-v2.0.34` (Latest; wheel, sdist, both installers,
`SHA256SUMS`) and `sdk-v0.7.15` (wheel, sdist).

## 2.0.33 / SDK 0.7.14

The installer and `mammoth upgrade` always reach the newest release. SDK
unchanged.

- The installers carry no embedded version: without `--version` they
  install, or upgrade to, the newest mammoth-cli on PyPI (index cache
  refreshed). The old release-time substitution also rewrote the
  placeholder check, so the "pinned" default never pinned.
- `mammoth upgrade` ran `uv tool upgrade`, which keeps an `==X.Y.Z` install
  on X.Y.Z; it now runs `uv tool install --force --upgrade`.
- `mammoth upgrade` finds the uv the installer keeps off PATH, so it works
  on a fresh macOS/Linux host with no uv of its own.
- CI gains the full offline suite on macOS and a macOS check that a pinned
  install, re-run, lands on the newest PyPI release.

CLI CI ran once before the release (Actions enabled for the run, then
disabled again): run 35974665866, all 11 jobs green — full suite on macOS
arm64 and Linux py3.12/3.13/3.14, installers on macOS arm64 and Intel,
Linux and Windows. `uv.lock` is tracked from this release on.

Published from deterministic local artifacts built from tag `cli-v2.0.33`
(source commit `7e30242`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.33-py3-none-any.whl` sha256 `3665952e7a499e57a9e2701091e55ae8a75307f513b5919078567e9adab14986`
- `mammoth_cli-2.0.33.tar.gz` sha256 `76db382ceb58caefc0e99d99e43b5adf0d5c2461afad5bd9eafd853827468138`

GitHub release `cli-v2.0.33` (Latest) carries these, both installers and
`SHA256SUMS`. Checked after publication: the release installer URL moved a
pinned 2.0.31 install to 2.0.33 with no uv on PATH.

## 2.0.32 / SDK 0.7.14

Fixes a login that never finished on macOS ("it's looking for secret"), plus
an audit of the skill, docs and core commands.

- Keyring calls are bounded: the CLI says what it waits on after 2 s and stops
  after 60 s. An interactive `auth login --storage auto` then stores the
  credential in the owner-only file and says so; any other command fails with
  `keyring_unresponsive` (recovery `mammoth auth login --storage file`). A store
  is read back before it counts; a profile in the file store is read without
  asking the keyring; the null/fail backends count as no keyring.
- Installed skill copies follow CLI upgrades (`skill-synced-version` marker);
  `skill update` with no agent touches only recorded installs; `skill list`
  and `doctor` report stale copies.
- `doctor` passes in an empty workspace and points at `project ensure`.
- Column errors name the column; a bad math token is named with scope
  `expression`; strict type errors read correctly.
- An all-text CSV upload that the backend ingests without a view returns
  `needs_view` with `next_command` `mammoth view create DATASET_ID`.
- SDK 0.7.14: a transform returns `"status": "done"` and
  `"pipeline_state": "ready"` after the pipeline wait (draft mode unchanged).

Published from deterministic local artifacts built from tags `sdk-v0.7.14`
(source commit `24be6f5`) and `cli-v2.0.32` (source commit `b49de57`). PyPI
reports the uploaded local artifact hashes:

- `mammoth_io-0.7.14-py3-none-any.whl` sha256 `ec06192119e0dec17ef12e0202c7d3c11228fecd04dea5dadb61d43e360e50c2`
- `mammoth_io-0.7.14.tar.gz` sha256 `113ed1151e0ede35da5817ca15d9b33d3b350ddc4dd251348daf97eb3ec2fd30`
- `mammoth_cli-2.0.32-py3-none-any.whl` sha256 `f3dfe14c4ce0a07740af281045c688cc383a4d94a10a967a1e86cdb9298491dc`
- `mammoth_cli-2.0.32.tar.gz` sha256 `a8471c64b3093d463d392b8b8f32b59b1dba24a1409e805089b3469b8b00a692`

A fresh install from PyPI resolves `mammoth-cli 2.0.32` with `mammoth-io 0.7.14`.

## 2.0.31 / SDK 0.7.13

The ILG shape rebuilt end to end on a second environment (prague ws 4) with
fresh mock data and the production procedure — `--dry-run` before every
write, `expected_task_count` on every pipeline write — 126 commands, 68/68
checks against the fixture key (`docs/capability-evidence/ilg-prague-20260921/`).
SDK unchanged.

- Start-up 2.44 s → 0.51 s: manifests parsed with libyaml and cached as JSON
  under the OS cache directory keyed by file size/mtime
  (`MAMMOTH_CLI_MANIFEST_CACHE=0` bypasses); top-level command groups are
  converted to Click on demand. Tree walkers and `--help` are unchanged
  (`tests/unit/test_startup_cost.py`). What remains per call is one TLS
  handshake and 1–1.3 s of server time per request, measured identically on
  release and prague; the SDK's eager import (~0.3–0.5 s) is the next lever.
- Recipes: `view export csv` input shape; `dataset get` nests the record
  under `data.dataset`; prague flags ISO dates as ambiguous and takes minutes
  to resolve; the cost of the dry-run procedure stated in safety.

Published from deterministic local artifacts built from tag `cli-v2.0.31`
(source commit `3f061db`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.31-py3-none-any.whl` sha256 `17410859c4653060f3287289951013dc4b221207d7487823e43d17549fc2ae45`
- `mammoth_cli-2.0.31.tar.gz` sha256 `7c6239ef3227398bd241d592603bc38ac687152622bc55442747816405ea48fc`

## 2.0.30 / SDK 0.7.13

The two safety items queued from the Loops/PostHog peer review, both proven
live (`docs/capability-evidence/dryrun-precondition-20260920/`). SDK
unchanged.

- `--dry-run` (global option on every API-backed command): the command is
  admitted, parents resolved, columns and conditions validated against the
  live view, then the SDK call is reported as `data.would_call` instead of
  made. The gate that stops it also stops any SDK write the command's
  manifest does not declare, so a dry run cannot mutate through a side
  path; reads pass. No confirmation flag is needed for a dry run.
- `expected_task_count` on `view transform *` and `view task add`: the CLI
  re-reads the task list right before the write and refuses with
  `pipeline_changed` (exit 2, `actual_task_count`, `task_ids`, recovery
  `view task list VIEW`) when the count differs from the one read. This is
  what makes "add only, never disturb an existing step" checkable on a
  shared pipeline (ILG gap 2).
- `extract-date` and `window` proven with read-back; REL-461
  `proven_transforms` now lists twelve typed transforms.
- `tests/contract/test_skill_hygiene.py`: every bundled-skill file is checked
  for invisible/bidi characters, injection phrasing, shell-pipe installs and
  unknown link hosts; the sweep it encodes found nothing.
- Skill/docs: safety reference ("Rehearse before you write", "Add-only edits
  to a pipeline someone else may touch"), operations, input, `docs/safety.md`.

Published from deterministic local artifacts built from tag `cli-v2.0.30`
(source commit `6bf3f43`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.30-py3-none-any.whl` sha256 `717a24eadb519c6c50c787e282edc016bcb8a31c593556ecd7cc47c29cb49fbb`
- `mammoth_cli-2.0.30.tar.gz` sha256 `863b81347b325170843c471b20791ab12431816a68643f7322981633084fcc95`

## 2.0.29 / SDK 0.7.13

The ILG rebuild brief, simulated end to end on release
(`docs/capability-evidence/ilg-sim-20260919/SUMMARY.md`), and what it taught
the docs. SDK unchanged.

- Proven live in owned projects 57/58/59: sends from two source projects
  into a target as pipeline steps (re-run on upstream change, pre-existing
  export untouched), `add-sql` conform per fact + three joins into a
  mixed-grain consolidated table, `dashboard canvas save` with a
  `countDistinct` KPI card, `measure2` bar, derived ratio line, table and
  range/multi filters, `dashboard descriptor-data` under a Month range
  (111 / 64 / 110 distinct staff against the fixture key), `dashboard pages
  add`. All four gaps in the feasibility review are closed or narrowed;
  `docs/production-readiness.md` carries the new list.
- `--input @FILE` is accepted (curl/gh convention); an `@` value that names
  no file still errors with the typed value.
- Recipes: "Authoring a board from a blank canvas" (page-level focus,
  derived measures, bindings read-back, `descriptor-data`), `add-sql` facts
  (single view; NUMERIC/TEXT/TIMESTAMPTZ result types; UNION ALL). Manifest
  `known_restrictions` on `view.transform.add-sql`, `dashboard.canvas.save`,
  `dashboard.pages.add`, `dashboard.descriptor-data`,
  `dashboard.create-blank`; runnable examples for `pages add` (PageAdd
  objects, `--yes --confirm`) and `descriptor-data` (`filter_state`).
- Matrix: 13 rows folded from the run; REL-461 `proven_transforms` gains
  `add-sql`.

Published from deterministic local artifacts built from tag `cli-v2.0.29`
(source commit `63bccdd`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.29-py3-none-any.whl` sha256 `3eb3fb83861336a1557739ba1511b48679f143d6e8e83eb314c00243a18a3244`
- `mammoth_cli-2.0.29.tar.gz` sha256 `2cb971309248a8c29d0257e7a3d5110de016c3e3f506ce1b4cc19a1a6ea6160f`

## 2.0.28 / SDK 0.7.13

Cross-project send, the first blocker in the ILG feasibility review, proven
live and made a typed route (`docs/capability-evidence/cross-project-send-20260919/`).

- SDK 0.7.13: `View.to_dataset(...)` / `branch_out(...)` take
  `target_project_id`. The backend's internal_dataset export needs
  `USER_ID`, `export_project`, `project_id` and `source_project_id` in
  `target_properties` for a cross-project write (it checks the caller's
  dataset-create permission on the target; without them the answer is
  4GENR007 with no detail). The SDK reads the user id once from `/self`.
- `mammoth view export dataset VIEW --yes --input '{"dataset_name": ...,
  "target_project_id": N}'` returns `{dataset_id, project_id,
  source_view_id, next}` instead of a bare integer, so the next read is in
  the envelope. The send is appended with `end_of_pipeline: true`, and the
  fixture run shows the target re-materialising (302 → 301 rows) when a
  filter is added upstream: it is a persistent pipeline step, not a copy.
- Exports recipe: new section "Send a view into another project"; manifest
  restriction on `view.export.dataset` records the result shape and the
  cross-project field.
- Matrix: REL-458 (AddExport) moves Unassessed → Partial on this evidence;
  the typed `view.export.dataset` route is a convenience over the same
  operation and has no row of its own.

Published from deterministic local artifacts built from tag `cli-v2.0.28`
(source commit `399544d`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.28-py3-none-any.whl` sha256 `0391a5dd8cec9088623a906174860196f2bab7a7495ee4e23eb012e692593c9f`
- `mammoth_cli-2.0.28.tar.gz` sha256 `3dabcc993482cd5a27b4a2985303ef56c6884853ab59f602003195e457de55f0`
- `mammoth_io-0.7.13-py3-none-any.whl` sha256 `f0991e22e72022f66802aa0c6a7e4df63a34b8e1675a4f4a3206a790037e1fff`
- `mammoth_io-0.7.13.tar.gz` sha256 `a269c76ed1db06c39760a0c949da88157133b1b3091eb3efee5ae39ba1c8ea9a`

## 2.0.27 / SDK 0.7.12

Two onboarding commands taken from a review of the Loops and PostHog agent
CLIs (`think/mammoth-cli-readiness/research/agent-cli-peers-20260919.md`).
SDK unchanged.

- `mammoth skill show` prints the bundled `SKILL.md` (or one reference file
  with `--input '{"file": "references/recipes/transforms.md"}'`) as
  `data.text`, so a cold start loads the guide with one command instead of
  `skill path` → parse → `cat`, which both Haiku runs did.
- `mammoth skill agents-md install [--input '{"path": "CLAUDE.md"}']`
  writes one `<mammoth-cli>…</mammoth-cli>` steering block into `AGENTS.md`
  (created, appended, or replaced in place; `unchanged` when current), the
  way `posthog-cli api agents-md install` does, so upgrading the CLI and
  re-running refreshes stale instructions without duplicating them.
- Both READMEs, `docs/agent-prompt.md`, `docs/agents.md` and the skill's
  task-start reference now say `mammoth skill show`.

Also in this release: `docs/production-readiness.md`, the one-page verdict and
evidence map, and `docs/capability-evidence/ilg-feasibility-20260919.md`.

Published from deterministic local artifacts built from tag `cli-v2.0.27`
(source commit `c5f16b1`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.27-py3-none-any.whl` sha256 `f7aa720118b629847a22da0de6d3c01000b0db7449b15a4923b2fa6f09564638`
- `mammoth_cli-2.0.27.tar.gz` sha256 `e1b7bf447ed7cc2e2da360b895ff7ece3a1b4cd4bae03e9f1f7edbdd5b912f6c`

## 2.0.26 / SDK 0.7.12

The SDK side of the 2.0.25 reference-error finding, and an upgrade fix
seen while checking that a 2.0.24 install learns about 2.0.25.

- SDK 0.7.12: `View._add_task` reads the server's draft flag *before*
  submitting (the backend flips it on a reference error, which is what made
  every transform skip its pipeline wait and report `has_error: true` as
  success) and raises `MammothTransformError` on a `has_error` result. The
  CLI enriches that error into the same `pipeline_reference_error`
  envelope (column, type, reason, `view task delete ... --yes`) it builds
  for older SDKs; verified live on a fresh view (probe project 56, deleted).
  `mammoth-io>=0.7.12,<0.8`.
- `mammoth upgrade` and `MAMMOTH_AUTO_UPGRADE` decided the package manager
  from `uv tool list`, so a plain venv on a host that also had a `uv tool`
  install "upgraded" the uv copy and kept running the old version. The
  decision is now about the running environment only: `sys.executable`
  under a uv/pipx tools directory, or `sys.prefix` under `uv tool dir` /
  pipx's venvs directory; otherwise pip in the running interpreter.
- Verified on a 2.0.24 venv: the daily check writes `update-check.json`
  after the first command, the next envelope carries
  `meta.update_available` `{current, latest, command: "mammoth upgrade
  --yes"}`, human output prints the one-line hint on stderr, and
  `MAMMOTH_AUTO_UPGRADE=1` upgrades before the command (opt-in).

Published from deterministic local artifacts built from tag `cli-v2.0.26`
(source commit `0580f31`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.26-py3-none-any.whl` sha256 `2a67da18e28544082e3889c31ff658483f9a0148ad387494417f474b4444f0bf`
- `mammoth_cli-2.0.26.tar.gz` sha256 `3ceb63f28d1107ec3fa35571d6b177989fd04564fe97680c1bc3526809fe9af8`

SDK 0.7.12 (`sdk-v0.7.12`, source commit `0580f31`): `mammoth_io-0.7.12-py3-none-any.whl` sha256
`994e1fcb46d5ecc96d8c83b09583e8b3bf8364fd79332a01d94e159d3b1a9eb8`; `mammoth_io-0.7.12.tar.gz` sha256 `a084fa8030c1784c5f50f9ede50ba4be32ed4516b304df69fdd0bd4d09075cc0`; digests verified against PyPI.

## 2.0.25 / SDK 0.7.11

Payload fixes for the three routes the 2026-09-19 sweeps left as "500 on
release", verified by reading the apiv2 tracebacks on the release host and
re-running the calls; SDK unchanged.

- `view derivative create`: the METRIC `ARGUMENT` must be the column's
  internal name (`metadata[].internal_name` from `view get`, e.g.
  `column_1`); a display name raises `KeyError: 'column'` in the backend.
  Example and hint now show an internal name; `known_restrictions` says so.
- `view derivative data`: the body is `{"condition": ..., "limit": null}`,
  what the web app posts; `{"limit": null}` is the minimal accepted body and
  `{}` is 4GENR007. The example used a `FILTER_TYPE` condition alone.
- `dashboard template create` restriction: the dashboard must bind columns
  ("None of the columns this template binds are in the dataset" on a blank
  one). `view data-check update`: the body equals the web app's; the 500 is
  backend validation after commit, so read the check back before retrying.
- A transform whose task the backend stores with a reference error (a
  find/replace on a NUMERIC column, a missing column) no longer reports
  success: the SDK reads the draft flag after the submit and the backend
  flips it on a reference error, so the job result `has_error: true` came
  back as exit 0 while the view sat in `ref_error` answering 4DTVW019 to
  every read. Transforms and `view task add` now fail with
  `pipeline_reference_error` (column, type, reason, `pipeline_state`) and
  the exact `view task delete VIEW_ID TASK_ID --yes` that repairs the view.
  Found by the second Haiku ETL run (`haiku-etl-20260919/REPORT-2.md`).
- `schema find` splits hyphenated ids, so `date` finds `extract-date`,
  `date-diff` and `increment-date`; the ETL transforms carry purpose words
  (`month`, `multiply`, `upper case`, `summary per region`). `pivot`,
  `replace` and `bulk-replace` carry their column-type / `as_name` rules.
- Release host finding (operational, not a CLI change): every "flapping"
  upload, stuck job (667, 693/694/699, 708–712 remain `processing`) and read
  timeout of 2026-09-19 traced to the root disk at 100 %, which raised the
  RabbitMQ disk alarm and blocked publishers, so jobs were created but never
  dispatched. ~5.5 GB of caches and journal were reclaimed (disk 82 %); uploads
  complete in ~16 s again. The volume needs to grow or `~/data/duckdb_efs`
  (2.1 GB) and `~/mmfiles/resources` (3.8 GB) need to move off it.

Published from deterministic local artifacts built from tag `cli-v2.0.25`
(source commit `b02c78b`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.25-py3-none-any.whl` sha256 `64a195faf39905ff2b49a822fd61adc665c36d4f36cf859a1b1fc287ca522c8b`
- `mammoth_cli-2.0.25.tar.gz` sha256 `2c9e11e4cb6422b8b8b0dfe479e7245f3b69e16c0e475e5c0a09c2ce0521efa4`

## 2.0.24 / SDK 0.7.11

From a Haiku 4.5 cold start on 2.0.23 with a complex ETL brief
(`docs/capability-evidence/haiku-etl-20260919`; blocked by the release upload
worker after two uploads, see its REPORT.md) and the operator's follow-up.
SDK unchanged.

- `view get` returns the brief record by default (id, ds_id, name, status,
  row_count, column_count, `metadata`, pipeline state) through the route's
  server-side `fields` projection: 7.5 KB → 1.5 KB on a three-column view.
  `--input '{"fields": "__full"}'` (or `"__standard"`, or a comma list)
  returns the rest. `fields` was handled but undeclared, so strict validation
  rejected it. `view list` records are trimmed to the same shape
  (10.9 KB → 2.2 KB for two views); `full: true` keeps them whole.
- Docs: the agent prompt and the upload recipe said `--timeout 300` for long
  operations; the job budget is `--job-timeout` (300 s by default since
  2.0.21). The recipe also states that re-uploading a stuck file queues a
  second job, and that `project list` can still show a project whose delete
  was accepted (202) until the worker runs it.
- Evidence index lists `ergonomics-sweep-20260919` and `haiku-etl-20260919`.

Published from deterministic local artifacts built from tag `cli-v2.0.24`
(source commit `bd83f46`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.24-py3-none-any.whl` sha256 `7a5bc05012c5bcd96d34a251e234fb480bb9abdbee8bbafc04a9c25b30f4a0d5`
- `mammoth_cli-2.0.24.tar.gz` sha256 `c50cd935bd08a3458e2b286f7e3c82563996767e3d20562087cf965647e95547`

## 2.0.23 / SDK 0.7.11

One fix from running the 2.0.22 onboarding lines as a fresh user: `doctor`
reported `config_directory` not writable on an account with no `~/.config`
yet, because it tested only the missing parent. It now judges the nearest
existing ancestor (where the first login creates the chain). SDK unchanged.

Published from deterministic local artifacts built from tag `cli-v2.0.23`
(source commit `e9796b8`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.23-py3-none-any.whl` sha256 `646360a727095eeb0bf354f202d64f76ceab433b772a530bfdfce727df2cd9a2`
- `mammoth_cli-2.0.23.tar.gz` sha256 `1072efc4289d1faf31af3ebe489e30a41017b86393fdd6aff4747dc81c56c6ca`

## 2.0.22 / SDK 0.7.11

Evidence and onboarding. SDK unchanged (`mammoth-io>=0.7.11,<0.8`).

- Capability matrix: the 2026-09-19 ergonomics sweep on release
  (`docs/capability-evidence/ergonomics-sweep-20260919`, 27 calls in owned
  projects 44–47, all deleted) is folded in: 259 Partial / 266 Unassessed.
  Newly verified: `batch create` (accepted as a job when the source is a
  standalone dataset), `ai suggestion list`, `file upload` with
  `append_to_ds_id` (row_count 3 → 6). Still backend-side: `browse`
  500, `schedule` NOT_IMPLEMENTED, `dashboard template create` 500,
  `view derivative create` 500 today, `view data-check update` 500 after
  applying, `ai sql generate` 4DTVW029 on a fresh dataset.
- Examples corrected from that run: `parameter create` uses
  `param_type: "TEXT"` (backend accepts NUMERIC|TEXT|DATE, 4PARM008
  otherwise); `view data-check create` carries `pinned_to_end: true`
  (4GENR007 "Either task_sequence or pinned_to_end must be set");
  `view data-check update` shows `{op: command, path: disable, value: null}`;
  `batch create` states that `SOURCE_ID` is a standalone dataset. The same
  shapes are the `--input` hints.
- Agent prompt (both READMEs and `docs/agent-prompt.md`): onboarding first.
  The agent installs the CLI when `mammoth --version` fails, and when
  `auth status` shows no credentials it prints a verbatim message telling the
  operator where to create an API key and to run `mammoth auth login` in
  their own terminal, then waits; `PROFILE` is no longer a placeholder (the
  default profile and `app` server are the defaults, named ones are added
  on request).

Published from deterministic local artifacts built from tag `cli-v2.0.22`
(source commit `473453d`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.22-py3-none-any.whl` sha256 `109511c4b1139e24328f83f3de9f05c87be81ec0f9ceaaaef81d1f5efa16e3ae`
- `mammoth_cli-2.0.22.tar.gz` sha256 `79380584c215a3ca110c07c56e14022eca07eac2ecf3b5935567c42c409b1601`

## 2.0.21 / SDK 0.7.11

Ergonomics. The agent runs seldom-changing choices once and every call after
that is short; output costs as few tokens as the answer needs. SDK unchanged
(`mammoth-io>=0.7.11,<0.8`).

- Output: JSON is one compact line when stdout is a pipe or file and indented
  on a terminal (`MAMMOTH_JSON_PRETTY=1|0` overrides). `meta` carries only
  keys with a value; `pagination` and `update_available` appear when set
  instead of as `null` on every envelope.
- Session defaults: `MAMMOTH_PROFILE`, `MAMMOTH_PROJECT`, `MAMMOTH_OUTPUT`,
  `MAMMOTH_NO_INPUT` stand in for the flags of the same name. Profile settings
  saved with `config set` (`output`, `timeout`, `job_timeout`,
  `pipeline_timeout`) are now applied to a run, as documented; before 2.0.21
  they were stored and ignored. Flag beats environment beats profile.
- `project ensure NAME` saves the project as the profile's active project
  (`data.active`), so `--project` is not repeated on every call.
- View commands: the CLI remembers which dataset each view belongs to
  (`view list`, `view get`, and any resolved call feed a small local cache
  under the config directory; `MAMMOTH_PARENT_CACHE` relocates it), so
  `view transform ...`, `view data get`, `view export ...` take the view id
  alone once the parent has been seen. The discovery walk remains the
  fallback.
- Waiting commands (transform, export, upload, job wait, ...) default to a
  300 s job budget; reads keep the request timeout. `--timeout` still wins.
- `schema list` returns a family index (`{family: [command ids]}`, ~1.5 KB
  instead of ~3 MB); `schema list FAMILY` lists one family's summaries;
  `--input '{"full": true}'` returns the old document. `schema get` returns
  the brief form (positionals, input fields, restrictions, example) and
  `--input '{"full": true}'` the JSON Schema. `--help` on any leaf lists its
  input fields with types.
- `view data get` returns at most 50 rows (`limit`; `0` for all) and reports
  `rows_returned`, `rows_total_in_page`, `truncated`; it forwards `sequence`,
  `timeout` and `poll_interval`.
- Every example, hint, recovery command and doc drops `--output json
  --no-input`; contract tests now reject those flags instead of requiring
  them. `SKILL.md` and `recipes/end-to-end.md` are rewritten around the
  short flow (doctor → project ensure → upload → view list → transform → data
  get), and `docs/agent-prompt.md` exports the two session defaults once.
- Errors: HTTP 502/504 (and 408/425) on a read map to `retryable_error`
  (exit 7) like 503; the same status on a write stays `outcome_unknown`.
  `project get` on an id that no longer exists is `resource_not_found`
  (was `api_error` with the SDK's `ValueError`, whose message listed every
  visible project). `doctor` distinguishes a disabled update check from an
  unreachable PyPI. View-scoped envelopes (`view transform ...`, `view get`)
  now report the effective `meta.project_id` like the project-scoped ones.

Verified live on release after the outage: doctor → `project ensure`
(created, active) → `file upload` → `view list` → `view get`, `view data get`
(3 rows, `truncated: false`; `limit: 2` → `truncated: true`) and `view
transform filter` with the view id alone (parent taken from the cache written
by `view list`) → read-back 2 rows, `row_count` 2 → `project delete` of the
smoke project only, then `project get` → `resource_not_found`. `schema get
view.transform.filter` 1.3 KB, `schema list` 1.6 KB, `schema list view` 16 KB.

Published from deterministic local artifacts built from tag `cli-v2.0.21`
(source commit `08c806c`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.21-py3-none-any.whl` sha256 `4408a08825a37c92d98d0c03a2b56eb262d79190e247afbea6d86e00c3bf8d1d`
- `mammoth_cli-2.0.21.tar.gz` sha256 `befca8a99e348d10e175547a97bf28f1dc41da91509e5577a7045dfcb668d85f`

## 2.0.20 / SDK 0.7.11

A follow-up to 2.0.19 for one thing the live run showed: the projects route
caps `limit` at 100 (`4GENR007` above it), so `project ensure` could not see
past the first hundred projects and refused to create in that case.

- SDK 0.7.11: `ProjectsAPI.list(offset=...)` (server-side) and
  `ProjectsAPI.list_all()`, which walks the 100-row pages and stops if the
  server ignores the offset; `ProjectsAPI.get(project="name")` searches every
  page.
- CLI: `project ensure` matches against every page before creating; the
  `conflict` refusal on a full page is gone. `list_projects` in the service
  layer pages server-side instead of asking for `limit + offset` rows.
- Docs: `docs/agent-prompt.md`, a paste-ready prompt that gives an agent
  Mammoth through the CLI in bash (install, read the shipped skill, operator
  login, `project ensure`, JSON envelopes, read-back); linked from the README
  and the agents guide as the recommended handover.
- The CLI requires `mammoth-io>=0.7.11,<0.8`. No other change from 2.0.19.

Published from deterministic local artifacts built from tag `cli-v2.0.20`
(source commit `9d525d1`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.20-py3-none-any.whl` sha256 `783fa80615502070da906d584d0716024d21ff9c5f88640d4824d7d0cff08db1`
- `mammoth_cli-2.0.20.tar.gz` sha256 `81dc62d4c9006173da9a07ce32342ae8c45f99bef129c597d50b9d55fa54d371`

SDK 0.7.11 (`sdk-v0.7.11`, source commit `07ca71a`): `mammoth_io-0.7.11-py3-none-any.whl` sha256
`a0659854b869cceaded7da3b1a4da24c3fd03b97bf1e05d44dc0ba0894ec1831`; `mammoth_io-0.7.11.tar.gz` sha256 `db7387c8890e006796ceb6fa93ff75b191ada5b7caa5e2f80a291da68d4bdc44`; digests verified against PyPI.

## 2.0.19 / SDK 0.7.10

This release turns the 2026-09-19 evidence into contract: what an agent can
upload, where its work lands, and how it learns a newer CLI exists. SDK
unchanged (`mammoth-io>=0.7.10,<0.8`).

- CLI: a once-a-day update check. Every success envelope carries
  `meta.update_available` (`null`, or `{current, latest, command}`); human
  output modes add one stderr line. The check reads a cached answer and
  refreshes it after the command's own output with a 3 s timeout, so no
  command ever waits on PyPI. `MAMMOTH_NO_UPDATE_CHECK=1` disables it;
  `MAMMOTH_AUTO_UPGRADE=1` (opt-in) upgrades before the command through the
  same manager detection as `mammoth upgrade`, once per release; `doctor`
  reports installed vs latest. The skill tells agents to run the returned
  `command` when `update_available` is set.
- CLI: `project ensure NAME`, an idempotent get-or-create by exact name
  (`created`, `duplicates`), for the "one working project per agent"
  convention the recipes now use (`project ensure 'From Claude'`). The
  projects route caps `limit` at 100 (`4GENR007` above it); with a full page
  and no match the command refuses to create blindly (`conflict`).
- CLI: `file upload` names a missing local path as a usage error before any
  request (the sweep's bare `ValueError`); HTTP 413 from the ingress maps to
  `invalid_argument` with a split/compress hint. The contract now states the
  accepted extensions (backend list; not `.json`) and the measured size
  boundary: 60 MB refused with 413, 16 MB accepted.
- CLI: strict input validation accepted only floats where the backend schema
  says `oneOf [number, integer]` (`data-check create` `threshold: 5`
  rejected); integral values now pass.
- Examples: `view checkpoint create` shows `pinned_to_end: true` (the backend
  requires a placement); `view exportable-config apply` states that `config`
  must be the full `get` document, not `{"tasks": []}`.
- Skill: pivot output names must not reuse an existing display name
  (`4DTVW018`); upload boundaries and scratch-project conventions in
  resources.md; `docs/upgrade.md` documents the notice and the opt-in
  auto-upgrade (the curl installer section is gone).

Live evidence this release: a Haiku 4.5 cold-start run
(`docs/capability-evidence/haiku-cold-20260919`: upload, clean, join, pivot,
export and cleanup from the shipped skill alone; 0 CLI or doc bugs, friction
notes folded into the recipes) and the upload size probe in an owned project
(60 MB -> 413; 32 MB and 8 MB -> bare 500 while the upload service was
degraded; 16 MB accepted as job 667, still `processing` when the probe
stopped). During the probe the release upload path stopped answering even a
50-row CSV; reads were unaffected. Matrix unchanged at 258 verified of 528.

Published from deterministic local artifacts built from tag `cli-v2.0.19`
(source commit `5083a53`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.19-py3-none-any.whl` sha256 `574c55663a79acb71b904a7d53ab557d0cf10fdb0de2305ed9f13eb4b30e0643`
- `mammoth_cli-2.0.19.tar.gz` sha256 `a50f197edbd0e5e025b4c6bfd5d557a3a0d80ea713da695e6b2d59a46bb0f57f`

SDK unchanged at 0.7.10 (`sdk-v0.7.10`); digests verified against PyPI.

## 2.0.18 / SDK 0.7.10

This release adds an always-on local run log, folds the 2026-09-18 skill
review, and passes a new live golden-data gate on release
(`docs/capability-evidence/golden-20260919`: every value-changing transform
run once on an owned fixture and read back against a known answer). What the
gate and the review found, and what changed:

- SDK: structured `mammoth.http` / `mammoth.jobs` log records (method, path,
  status, duration, backend request id, job polls); no headers, bodies or
  credentials. Nothing is emitted unless a handler is attached.
- CLI: `mammoth log path` / `mammoth log tail` over a JSONL run log (one file
  per day, 0600, 7-day retention, 20 MB cap, `MAMMOTH_LOG_DIR` override);
  every error envelope carries `error.log_ref {file, run_id}`; `doctor`
  checks the log directory is writable.
- CLI: `view create` returned `"<unserializable View>"`; it now returns the
  new view's record (`id`, `dataset_id`).
- CLI: `view data query` forwarded the `{column, operator, value}` spec
  verbatim, which the data route rejects (`A clause can only have one key`,
  job failed). The condition is compiled to the backend clause shape with the
  view's internal names and types, and `columns` display names are mapped;
  verified live (EQ with column select; AND of CONTAINS and NE).
- CLI: an all-text CSV comes back `ready` with "more than one plausible way to
  be read" and no view; `file upload` now reports it as `need_action` with the
  settings command to run (recipe: need-action.md).
- CLI: `project delete` is `confirm_target` (`--yes --confirm PROJECT_ID`);
  `dashboard create-blank` no longer asks for `--yes`; `schema get` exposes
  `secret_fields`.
- Skill: recipes only route from SKILL.md; new end-to-end worked example and
  report checklist; recovery table by error message; ID glossary; cleanup
  verified for ids returned by your own run; exports that carry a secret go
  through `--input FILE` (0600) and `--yes`; per-entry release status lines in
  the command catalog; the release capability matrix ships as
  `references/capabilities.md` (core) and `capabilities-misc.md`.
- Recipes no longer build a summary on a `view create ... clone_from` copy:
  on release the clone job succeeds but the copy answers every read with
  `4DTVW019` and its copied tasks never execute (backend defect, recorded in
  `backend-repro-20260918/HANDOVER.md` together with the all-text CSV case).
  Export the cleaned rows first, then pivot in place as the last step.

Golden gate (CLI 2.0.18 on release, project created and deleted by the run):
bulk-replace, convert-type, set-values with IS_EMPTY, text trim/lower, filter
REMOVE, discard-duplicates, LEFT join, export csv, pivot — 23 value
assertions, all read back with `view data get`; `view data query` with a
condition on the pivoted view.

A fixture-lifecycle sweep the same day (`fixture-sweep-20260919`: one owned
project, 91 calls, every created id deleted and read back) added 31 verified
routes — webhook, automation, workflow, snippet, template, parameter,
checkpoint, data-check, derivative, batch and exportable-config lifecycles plus
the no-fixture reads. It also recorded, for the next release: `automation
update` documents `name` where the route takes `patch`; `file upload` with
`append_to_ds_id` raises a bare ValueError before any request; the checkpoint
and data-check create examples omit `pinned_to_end` / mis-type `threshold`;
`checkpoint update` needs a patches envelope. Backend-side: `schedule` routes
answer NOT_IMPLEMENTED, `automation get/list` cannot read a created
automation, `browse root/project` 500, `connector get` rejects the keys
`connector list` returns, `batch create` and `derivative data` 500 with an
empty body. The OpenAPI snapshot that ships in the wheel is now scrubbed of
credential-shaped example values (`sync_openapi.py --scrub`, enforced by
`--check`).

Matrix after this release: 258 verified of 528 (core workflow 191/230), 2
Not supported, 9 rows "CLI defect fixed" still awaiting a fixture or blocked by
the backend. The CLI requires `mammoth-io>=0.7.10,<0.8`, adds no API
bindings, and makes no capability-status or autonomous-workflow qualification
claim.

Published from deterministic local artifacts built from tag `cli-v2.0.18`
(source commit `63628bf`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.18-py3-none-any.whl` sha256 `1a7525988228882c5ed84ceee61d4eb425fbde171d70bd9423272eea48aa88f5`
- `mammoth_cli-2.0.18.tar.gz` sha256 `92ec23b98095712e75e5121c74b54c3fa6578e5d83262d1af3284ebb92437d4e`

SDK 0.7.10 (`sdk-v0.7.10`, source commit `8f3e0a0`): `mammoth_io-0.7.10-py3-none-any.whl` sha256
`b52c85c28d8107381078f848e6a10b4cfe455b0ca15c470412e6e6fdb28be3c6`; `mammoth_io-0.7.10.tar.gz` sha256 `f7f988396ef51109a18ef910ffddf28e755af426bdc19f884977f20b99640cb4`; digests verified against PyPI.

## 2.0.17 / SDK 0.7.9

This release folds a cold-start end-to-end run by a Claude Haiku agent
(install from PyPI, learn from the bundled skill alone, clean and join three
messy CSVs, summarise, export, one dashboard, cleanup; evidence under
`docs/capability-evidence/haiku-cold-20260918`) and the re-run of the routes
fixed in 2.0.16 (`reverify-216-20260918`):

- SDK: `set_values(condition=...)` emitted the condition at task level, which
  the backend's VERSION 2 `VALUES` form ignores, so a "fill blanks with 0"
  overwrote every row (the Haiku run delivered all-zero amounts and all
  "Unknown" regions without noticing). The condition is folded into each
  value item; verified live (only the blank row changed).
- SDK: `conditional_format_list()` returned `[]` for a view with rules
  (release answers `{rule_id: rule}`); rules now carry `rule_id`. With that,
  `view conditional-format delete-all` is verified live.
- CLI: `file upload` hard-coded `status: "ready"`; a CSV with an ambiguous
  date column lands in `need_action` with no view. The result now reads each
  dataset back and points at `dataset file-settings get` when action is
  needed.
- CLI: a discovery miss on `view get` / `view task list` (view deleted or in
  another project) surfaced as `api_error ValueError`; it is `not_found` (exit
  5) on every path now.
- CLI: an unknown option that names a real field says so (`--name` on
  `project create` is positional argument 1; `--dataset-id` on a transform is
  an `--input` field) instead of only pointing at the schema.
- Docs/skill: the SQL task references the view as the quoted table
  `"view:ID"` (or its quoted display name); `FROM data` / `__TABLE__` are
  rejected by the backend. SKILL.md states the input model (positionals +
  `--input` + global options, no per-field flags) and which view commands
  take the parent as a positional versus an input field; the transforms
  recipe gains an aggregation section and a read-the-data-back rule.

Matrix after this release: 227 verified of 528 (core workflow 187/230), 2
Not supported, 3 rows "CLI defect fixed in 2.0.16" still awaiting a fixture
(`batch create`, `view export publish-db-update`) or blocked by the backend
(`view task preview`). The CLI requires `mammoth-io>=0.7.9,<0.8`, adds no
API bindings, and makes no capability-status or autonomous-workflow
qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.17`
(source commit `be5da61`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.17-py3-none-any.whl` sha256 `9b7a2e0644d505965d98caaa81f594ddaa73ce1097dbf3d53bd61d3e996c7005`
- `mammoth_cli-2.0.17.tar.gz` sha256 `15259b6fa2880b5d16c756ece93de322a50cacee6b65e2d5a1d5da48f0da04b8`

SDK 0.7.9 (`sdk-v0.7.9`, source commit `e3cd46a`): `mammoth_io-0.7.9-py3-none-any.whl` sha256
`e51008949e82685605493892a716bc9008924b8067caf63b38d90148136817e3`; `mammoth_io-0.7.9.tar.gz` sha256 `e8b63413dbe5320ff6f9a2040ab0b68eef87a04bd9c7f1c8fdf8e5dd8101285d`; digests verified against PyPI.

## 2.0.16 / SDK 0.7.8

This release folds three 2026-09-18 runs on the published 2.0.15 build
(evidence under `docs/capability-evidence/reverify-215-20260918`,
`admin-read-sweep-20260918` and `backend-repro-20260918`) and repairs what
they found on the CLI side:

- Re-verification of the 27 routes marked "CLI defect fixed in 2.0.15": 19
  now verified live, 5 dispatch correctly but hit backend errors, 3 lacked a
  fixture. Three follow-ups: `view conditional-format delete-all` accepted
  `rule_id` but dropped it before the SDK call (now forwarded and required);
  `batch create` mapping items need `expected_destination_c_type` (the SDK
  stamps it on the `{src: dst}` shortcut and the example shows a full item);
  `view export publish-db-update` takes `{"odbc_type": "postgres"}` as the
  patch value, not a bare string.
- `view task preview`'s documented `COPY: {}` placeholder was rejected with
  backend code 720; the example now uses the backend param-template shape
  (`COPY` list of `{SOURCE, AS{COLUMN, TYPE, INTERNAL_NAME}}`, `VERSION` 2).
  With that shape the backend accepts the job and then fails serializing a
  DATE column, so the route stays a backend blocker.
- Admin/billing read sweep: 13 of the 30 GET routes verified (with the
  `--yes --confirm WORKSPACE_ID` gate the CLI puts on every support/billing
  command), 6 forbidden for an API key, 6 backend errors, 5 without a
  fixture. `support workspace list` returns a bare array; SDK 0.7.8 wraps it
  as `{"workspaces": [...]}`.
- Backend reproduction: nine defects confirmed with a second input each
  (checkpoint get/update 500, data-check update 500, derivative data 500,
  generic csv export job `'destination'`, PDF import 4DTSTO003, template
  create 500, generation-info 5GENR011, task preview serialization) plus
  `ai retention condition` 4PERM001. The handover with reproduction commands
  is `docs/capability-evidence/backend-repro-20260918/HANDOVER.md`.

Matrix after this release: 225 verified of 528 (core workflow 185/230), 2
Not supported, 4 rows "CLI defect fixed in 2.0.16" awaiting a re-run. The 73
operations without a CLI command and the 44 support/billing write routes
(subscriptions, charges, user registration) were not exercised. The CLI
requires `mammoth-io>=0.7.8,<0.8`, adds no API bindings, and makes no
capability-status or autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.16`
(source commit `5c115c3`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.16-py3-none-any.whl` sha256 `fecf5fe94f6436c6cfb29f9ed1adb39a86755bf2ebcf0236f2d0edf924f9219c`
- `mammoth_cli-2.0.16.tar.gz` sha256 `a7a95806b7b8f1fd9bf0e7b2ba2d5e4fa4213672b7a1a1249b89774c3bc48d21`

SDK 0.7.8 (`sdk-v0.7.8`, source commit `2df82ed`): `mammoth_io-0.7.8-py3-none-any.whl` sha256
`5bd01357df1fbf0d0898434701b52eacf9dc04d333b6fdb6f145516b6ac0d395`; `mammoth_io-0.7.8.tar.gz` sha256 `6c954e0dc7aabdd1346f9b0c3f6b0f26752db6354ecdd94919c3ca3f36fc9230`; digests verified against PyPI.

## 2.0.15 / SDK 0.7.7

This release closes the CLI-side defects the 2026-09-18 write sweep (79
mutating commands in disposable projects) and the dashboard re-verification
found on release (evidence under `docs/capability-evidence/write-sweep-20260918`
and `docs/capability-evidence/dashboard-reverify-20260918`):

- Seven writes that committed (`project delete`, `view checkpoint delete`,
  `view data-check delete`, `view derivative update` / `delete`, `dataset
  file-settings undo`, `workspace segment update`) reported `outcome_unknown`
  (exit 7) because the backend answered 2xx with a non-object body such as
  `202 Accepted`. SDK 0.7.7 returns those as `{status_code, response}` and the
  CLI reports success.
- Request bodies that did not match the release contracts (HTTP 400 `Field
  required`): `project update` (`patches`), `project user add` (`users` with
  numeric ids), `folder move` (`patch` with a `move` op), `user preference
  update` (`patch` list), `view task update` (`patches`), `batch create`
  (list `mapping`, `new_ds_details`, `validate_only`), `ai sql generate`
  (`dataset_id` query parameter), `ai suggestion list` (`suggestion_type` +
  `params`), `view ai profile` (`{"params": {"action"}}`), `connector query
  generate` (`query`, not `prompt`), `view conditional-format delete-all`
  (`rule_id`), `dataset bulk-delete` (`dataset_ids`, named in the
  confirmation). Input schemas, examples and the manifests follow the SDK.
- `dashboard published data` polled the job through `GET /jobs/{id}`, which
  answers 4PERM002 for published-dashboard jobs although the job succeeded;
  `wait_if_job` now takes a `fetch` seam and the published commands poll
  `GET /dashboards/url/{url}/jobs/{id}`.
- Arguments the SDK rejects before any request (`ai expression generate` with
  a mode other than `math`/`metric`, `batch update` ops other than
  `replace`/`remove`) surfaced as an empty `api_error`; they are
  `invalid_arguments` (exit 2) with the SDK's message now.
- `project bulk-update` confirmed "bulk-update projects in workspace N" with
  no visible target set; the body must now be a `ProjectsPatch` whose every
  value item names a `project_id`, and the confirmation lists those projects.
- Examples that could not run as printed: `view checkpoint update` (needs
  `value: null`), `view export publish-db-update` (only `path: credentials`
  with `postgres`/`bigquery`), `view pipeline edit` (allowed paths and value
  types are documented in the transforms recipe). `view conditional-format
  create` and `user preference update` no longer claim to be fail-closed:
  they dispatch, and the catalog says what the backend expects.

Not fixed here because they are backend behaviour, recorded in the matrix:
`view checkpoint get` / `update` HTTP 500, `view data-check update` HTTP 500,
`view derivative data` HTTP 500, `dashboard template create` HTTP 500,
`ai retention condition` 4PERM001, `dashboard published pdf` / `video export`
4PERM002, `view export create` job failure on a bare `'destination'` key,
`view task preview` needing internal column names, `dataset create-from-pdf`
requiring a table list. The CLI requires `mammoth-io>=0.7.7,<0.8`, adds no
API bindings, and makes no capability-status or autonomous-workflow
qualification claim. Fixed routes are marked "CLI defect fixed in 2.0.15" in
the matrix until they are re-run live.

Published from deterministic local artifacts built from tag `cli-v2.0.15`
(source commit `c195446`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.15-py3-none-any.whl` sha256 `6ec05a2c42d713690d8cd2f31dc5ecb990771dda135d4318539c286f3e91a217`
- `mammoth_cli-2.0.15.tar.gz` sha256 `aab8980167629dee27646e149227dbbfdb21a2c3bc1de680910493f62e6a8a57`

SDK 0.7.7 (`sdk-v0.7.7`, source commit `8a975f3`): `mammoth_io-0.7.7-py3-none-any.whl` sha256
`b02c0db9a83f2fa96839d499224a9f79590d6d124bea68f145093ca25d19f746`; `mammoth_io-0.7.7.tar.gz` sha256 `673460a5d1888d0c9ab9654ae98647d8d2dd3345631296ed3c1664413c93a23c`; digests verified against PyPI.

## 2.0.14 / SDK 0.7.6

This release closes the CLI-side defects the 2026-09-18 dashboard sweep and
the Haiku end-to-end run found on release (evidence under
`docs/capability-evidence/dashboard-sweep-20260918` and
`docs/capability-evidence/haiku-e2e-20260918`):

- Output redaction erased every key containing `token`, so `dashboard canvas
  get` returned `style_tokens: "***REDACTED***"` (breaking the documented
  canvas get → save round-trip with HTTP 400), and `dashboard style derive` /
  `dashboard style token list` returned nothing usable. Plural design-token
  keys (`tokens`, `style_tokens`, `styleTokens`) are data now; singular
  credential tokens (`token`, `access_token`, `accessToken`, `refresh_tokens`)
  stay redacted.
- `dashboard archive` reported `outcome_unknown` (exit 7) on an HTTP 200 whose
  body is a non-object JSON value, although the archive had committed. SDK
  0.7.6 accepts any 2xx JSON body on that undeclared-schema route (and on
  `share`); the CLI returns `{dashboard_id, archived, response}`.
- `dashboard data draft` / `dashboard data published` sent `{"sql": ...}`;
  the route takes a `WidgetDataSpec` (`{"params": {"widget_id", ...}}`) and
  answered HTTP 400 `params: Field required`. SDK 0.7.6 takes `widget_id`
  plus optional `global_filters` / `drilldown_filters`; the CLI input schema
  and example follow.
- `dashboard figure-intent`, `dashboard template get` and `dashboard style
  default get` failed with an empty `ValidationError` envelope because the
  live response no longer matched the generated snapshot model. Generated
  wrappers now return an unmatched 2xx body unchanged, and any remaining
  pydantic failure names the model and the failing fields.
- Examples that could not run as printed: `dashboard query` (descriptor needs
  a `kind`; the example is now `{"kind":"scalar","agg":"count"}`) and
  `dashboard update` (`path` is a bare field name, not a JSON pointer; the
  example is now a title rename and the SDK docstring says so).
- Skill recipes: fill a blank with a literal via `set-values` + `IS_EMPTY`
  (`fill-missing` only propagates neighbours); `filter_type: "REMOVE"` to drop
  rows; `file upload` takes a positional path; `dataset delete` is
  asynchronous; canvas get → save round-trip; `dashboard pdf export` /
  `video export` need a browser-hydrated payload the CLI cannot build.

Not fixed here because they are backend behaviour, recorded in the matrix:
`dashboard source list` HTTP 500; `dashboard create` retired (HTTP 409
`4DASH012`, marked Not supported; use `create-blank` / `v3 generate`);
`dashboard pdf-artifact` reports "Dashboard not found" for a missing job id;
`dashboard pdf export` requires client-hydrated data (Not supported from the
CLI). The CLI requires `mammoth-io>=0.7.6,<0.8`, adds no API bindings, and
makes no capability-status or autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.14`
(source commit `83d16ff`). PyPI reports the uploaded local artifact hashes:

- `mammoth_cli-2.0.14-py3-none-any.whl` sha256 `6ad14c8d69ea1046a709152b9f598f91b9e58737b1f8c4d070e0cc1ab9b02467`
- `mammoth_cli-2.0.14.tar.gz` sha256 `c3a60cec295a8032f5ca9e4e71a5b9ebcbd21dbfce4be8c8cf602f921fcf50ff`

SDK 0.7.6 (`sdk-v0.7.6`): `mammoth_io-0.7.6-py3-none-any.whl` sha256
`9c4a523b8657c5faeb64282912816597ebbb24c357f2189512cd5507960c5945`; `mammoth_io-0.7.6.tar.gz` sha256 `8288c20278254b0ae7adbc8de1a7b1e072f430622c200aed762d654fe9669961`.

## 2.0.13 / SDK 0.7.5

This release closes the CLI-side defects the 2026-09-18 read-only sweep
found, each re-verified live on release before the fix and after it:

- `project resource-dependencies 3` failed with "No such command '3'": the
  path is also a group (`... update`), and Click resolved the positional as a
  subcommand name. Leaf groups now keep bare tokens as positionals and still
  parse the options that follow them; the subcommand is unaffected. The
  example carries integer `resource_ids`, which the backend requires.
- `view pipeline items-all VIEW_ID DATASET_ID`: the advertised trailing
  parent positional was ignored; it is honoured now and a conflicting
  `dataset_id` input field is rejected.
- `template list` and `connector ai session list` raised `api_error` on an
  HTTP 200 because those routes return a bare JSON array (SDK 0.7.5 wraps it).
- `dashboard og-card` and the other artifact reads raised `JSONDecodeError` on
  a 200 PNG/PDF/MP4/HTML body (SDK 0.7.5 returns a described body with
  `content_type`, `size_bytes`, `sha256`, and `text` or `content_base64`).

Not fixed here because they are backend behaviour, recorded in the matrix:
`browse folder 0` returns 400 although `folder root` reports id 0 and
`browse project` returns 500, so the project root cannot be browsed;
`schedule list` 400 "Not implemented"; `workspace user get` 405;
`connector get bigquery` rejects a key `connector list` returned;
`dashboard rls value list` and `dashboard data draft` reject inputs the
schema admits. The CLI requires `mammoth-io>=0.7.5,<0.8`, adds no API
bindings, and makes no capability-status or autonomous-workflow
qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.13`
(source commit `4600720`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `2818c1dbc767205531e5c82ab24abdbb0a4df8f9e81437db6201433f7b4a1219` |
| Source distribution | `cc37db4906529c890c89346c3197d5bfc5a0fd3a0beeb2f9660ce903aa831800` |

Before upload, the full non-live suite at the release source recorded
3,881 passed plus the 6 tests touched afterwards re-run green (3,887 total),
2 skipped, 7 deselected; SDK unit suite 1,824 passed; Ruff, mypy, and
`twine check` passed.

## 2.0.12 / SDK 0.7.4

This release exists to pick up mammoth-io 0.7.4, which fixes `dataset
rename`: the SDK sent a `rename_dataset` operation on the plural datasets
route that the server rejected with HTTP 400 for every caller, including the
documented CLI example. The SDK now sends the OpenAPI `DatasetPatchOperation`
(`replace`/`name`) to `PATCH /datasets/{dataset_id}`; the fix was verified live
on the release environment by creating, renaming, reading back, and deleting a
throwaway dataset. The CLI requires `mammoth-io>=0.7.4,<0.8`.

The bundled skill gains a `need_action` recipe: an uploaded CSV with
ambiguous dates stops in `status: need_action` with no views, and an agent
without guidance handed that to the operator's UI. The recipe shows the
CLI path observed live on release: `dataset file-settings get` (reports
`has_ambiguous_dates`), then `dataset file-settings update` echoing the
detected settings plus `date_format`, then polling `dataset get` until
`ready`.

The exact-parent rule now covers every non-read view command. In 2.0.8 it
was applied to the `view.py` family only; `view transform *` and `view draft
*` still fell back to the SDK's project-wide parent discovery when
`dataset_id` was omitted. On a large production project that discovery
browsed a folder that returned HTTP 500 (surfaced from a join) and, when it
did not find the view, raised a bare `ValueError` that the CLI flattened into
`api_error: The Mammoth operation failed unexpectedly` (surfaced from filter
and math with valid inputs). These commands now fail closed with
`missing_argument` and the `view get` read that supplies the parent; the
`dataset_id` input field is admitted for `view draft *` as it already was for
transforms; every generated transform/draft example carries `dataset_id`;
a join or lookup whose foreign view is given without `foreign_dataset_id` /
`lookup_dataset_id` is refused the same way instead of discovering it; and a
discovery miss on a read maps to `resource_not_found` with the reason and
recovery reads instead of the opaque failure. Verified live on release:
a transform without the parent is refused before any request, and with
`dataset_id` in `--input` it submits.

Two read-only local commands are new: `dataset find NAME_SUBSTRING` and
`folder find NAME_SUBSTRING` search every project the credential can see
(or only `--project`) by case-insensitive name substring and return
`project_id`, `project_name`, `id`, `name` per match plus
`projects_searched` and `projects_truncated` (the projects endpoint returns at
most 100). Both were exercised live on release. The bundled skill also states
the dataset-to-view hop (`view list DATASET_ID`), that no dataset-level
union/append transform exists (append is `file upload` with
`append_to_ds_id`), that `schema find` is local while `dataset list` is
per-project, and the three response shapes agents most often misread. The
release adds no API bindings and makes no capability-status or
autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.12`
(source commit `a4175d5`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `b42434869c55593c44d45d1f3c01bea2628fe4ee3e837a13f193f12884f073c7` |
| Source distribution | `206fcd4881abe2e5438d2be3011382671b0df204341fd15ba8c9ff42443fe7d1` |

Before upload, the full non-live suite at the release source recorded
3,884 passed, 2 skipped, 7 deselected; Ruff, mypy, and `twine check` passed.
The read-only capability sweep evidence (`docs/capability-evidence/read-sweep-20260918`)
and matrix update were committed after this tag and ship with the next release.

## 2.0.11 / SDK 0.7.3

This CLI-only diagnostics addition makes `doctor` answer "where can this
credential work", not only "does it authenticate". After the connection
check it reports a `projects` check listing the projects visible in the
workspace (id and name, first 20) and a `project_context` check stating
whether `--project` or the selected project is among them; a selected
project outside that list fails the run and recommends `project list`. No
selected project is reported but is not a failure, because every command
accepts `--project`. The API exposes no role or permission data, so the
check states that write access is not verifiable and is proven by the
first write. It retains `mammoth-io>=0.7.3,<0.8`, adds no API bindings, and
makes no capability-status or autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.11`
(source commit `ac1806a`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `577f86b333981d72e7c19fa2e349a84e35ae0dde10c069ba709b369bdced7165` |
| Source distribution | `68249f9dcefcdd7e401e17b3a65dc959d8b2680792b706f2907ddf8ff958f8be` |

Before upload, the full non-live suite at the release source recorded
3,861 passed, 2 skipped, 7 deselected; Ruff, mypy, and `twine check` passed.

## 2.0.10 / SDK 0.7.3

This CLI-only interactive-login correction responds to a field report that
the hidden prompts gave no feedback and a rejected pair gave no clue what
had been sent. Each hidden entry now strips surrounding whitespace (a pasted
newline no longer becomes part of the secret), rejects an empty entry before
any request, and prints a masked receipt to stderr (length and last four
characters, never the value). A rejected login now reports the endpoint base
URL, the workspace id, and a credential receipt in `details`, and its hint
states that credentials are per environment. Values are never echoed; the
output redactor still masks any credential-shaped field. It retains
`mammoth-io>=0.7.3,<0.8`, adds no API bindings, and makes no
capability-status or autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.10`
(source commit `052445a`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `a1c9faeee9e6ea4cd6ab097b0c220c5c49053633e3319800f0a6b4ec3be64fdf` |
| Source distribution | `ac52c6a8a11a9916d5cd60c0471fee7f4ced2759900b28c31202f8cc16a21812` |

Before upload, the full non-live suite at the release source recorded
3,860 passed, 2 skipped, 7 deselected; Ruff, mypy, `twine check`, and the
generated-doc check passed.

## 2.0.9 / SDK 0.7.3

The full non-live suite for the 2.0.9 source later completed with
3,857 passed, 2 skipped, 7 deselected.

This CLI-only login-persistence and onboarding correction responds to a
reproduced field report: after a successful `auth login`, `doctor` reported
`credentials present` but `no profile`, because the profile record and the
selection pointer were persisted in separate writes and the record was lost.
`auth login` now writes the profile record and the selection pointer in one
atomic write, before the secret is stored, and reads the record back; if it
is not readable the command fails with `profile_write_failed` instead of
reporting success. `set_selected` refuses a profile that has no record
(`profile_not_found`). The bundled skill and agent guide now give the
minimal production login (`mammoth auth login`; `--server-prefix release`
only for release) and state that credentials are per environment. It
retains `mammoth-io>=0.7.3,<0.8`, adds no API bindings, and makes no
capability-status or autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.9`
(source commit `6548a67`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `b944024049a4e47207a748093fdb1866e23026e43e9edf96cdc08ff16507a3dd` |
| Source distribution | `887d38a51fa9838b78a26ed0e6281c210efe1bc583b051daa2c87894d47fa056` |

Published at the operator's request before the full non-live suite
completed; focused auth/context/config/doctor tests (114), skill and doc
contract tests (716), Ruff, mypy, and `twine check` passed first. The full
suite result is recorded in the next entry when available.

## 2.0.8 / SDK 0.7.3

This CLI-only safety change closes the P0 from the 2026-09-17 systemic scope
audit. Thirty-nine `view` commands that change, export, or delete data
(16 benign mutations, 16 external-effect exports, 6 destructive commands, and
`view.exportable-config.apply`) previously accepted an omitted `DATASET_ID`
and fell back to the project-wide browse-and-probe parent resolver before
acting. They now fail closed with `missing_argument` (exit 2) and a
`recovery_commands` entry naming the `view get` read that supplies the
parent; `view.delete` fails with `resource_identity_required`. The
seventeen read commands keep parent discovery. The `DATASET_ID` help text
and generated reference say so for every affected command, and the bundled
skill and agent guide state the rule. Typed `view transform` commands keep
their existing SDK-side resolution when the parent is omitted; that path is
reversible and is unchanged in this release. It retains
`mammoth-io>=0.7.3,<0.8`, adds no API bindings, and makes no
capability-status or autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.8`
(source commit `1fa4ec0`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `c8d08c1ab4fe228d80ff20dbbb0b8265f4cd6815693b039235304894c90c44f9` |
| Source distribution | `e20bc5c80de52ec3e813baf23435b5ba711ea52e7ab4b49b6560ea5a29015143` |

Before upload, the full non-live suite at the release source recorded
3,852 passed, 2 skipped, 7 deselected; Ruff on `mammoth_cli/`, mypy,
`twine check`, and the generated-doc check passed. A fresh Python 3.14
environment installed the exact wheel, passed `pip check`, reported version
2.0.8, and returned the required-parent help from `schema get view.trash`.

## 2.0.7 / SDK 0.7.3

This CLI-only discovery-contract correction makes `schema get` and the
generated reference publish a protected `--input /private/path/request.json`
reference, instead of an inline `replace-with-secret` JSON body, for the
fourteen commands whose required request fields carry a secret
(`file.set-password`, `user.change-password`, `workspace.accept-invite`, and
eleven credentialed `view.export.*` targets). It also corrects the recorded
SDK signatures of `JobsAPI.get_job` and `JobsAPI.get_jobs` to the published
`mammoth-io` 0.7.3 (`timeout: float | None = None`), so discovery output and
introspection agree. Contract tests now accept the deliberate schema hand-off
example for blocked raw-patch commands (`dataset.update`, `view.update`) and
the manual-dispatch publication policy. It retains `mammoth-io>=0.7.3,<0.8`,
adds no API bindings or request-execution path, and makes no
capability-status or autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.7`
(source commit `f4bf6c1`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `7b646c52737857ed90b38c4e633cc51f5cc44a1b26567aad8a6b964064780ca6` |
| Source distribution | `ac976b2e15f8e1aac5ca4cdb6be25d1ad0d1fa165449a180a573bb3c1bf8395b` |

Before upload, the full non-live suite at the release source recorded
3,846 passed, 2 skipped, 7 deselected, with the only failure being the
in-flight version-metadata check that passed after reinstalling; Ruff,
mypy, `twine check`, and the generated-doc check passed. A fresh Python 3.14
environment installed the exact wheel, passed `pip check`, reported version
2.0.7, and returned the protected-file example from
`schema get file.set-password`.

## 2.0.6 / SDK 0.7.3

This CLI-only bundled-skill and documentation correction closes the agent
credential hand-off gap. A fresh agent given the onboarding prompt found no
sanctioned way to obtain credentials from its operator, so it invented one
("environment credentials", which the CLI never reads). The skill, the
`agents`/`authentication`/`quickstart` guides, and the copy-paste onboarding
prompt now instruct an agent to stop, hand the operator the exact
hidden-prompt `mammoth auth login` command to run in their own terminal, and
wait; they state that the CLI reads credentials only from the current login or
the selected profile store. The evaluation-harness "controller broker/sidecar"
instructions are removed from the shipped skill and public docs. It retains
`mammoth-io>=0.7.3,<0.8`, adds no API bindings or request-execution path, and
makes no capability-status or autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.6`
(source commit `bd14538`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `769d04236c3bf3518fbe8c8731cbb6695891e8c540897baad225e2a803b5360f` |
| Source distribution | `5921d27dfe5f30ef00e12fba8efdb5cf6631a7dc92a655b13d5af453bfedd8a9` |

Before upload: skill/packaging/README-doc contract tests (87), the
doc-example, STE, and version tests (711), Ruff on `mammoth_cli/`, mypy, and
`twine check` passed. A fresh Python 3.14 environment installed the exact
wheel, passed `pip check`, reported version 2.0.6, and returned
`has_credentials=false` from `auth status` for an empty home. The full
non-live suite at the parent commit had four unrelated pre-existing failures
(manifest example drift in `dataset.update`/`file.set-password`, SDK
introspection for `JobsAPI.get_job`, and the release-workflow trigger test);
they are recorded, not fixed, in this release.

## 2.0.5 / SDK 0.7.3

This CLI-only documentation and bundled-skill correction makes the secure
authentication preflight and schema-first command discovery explicit, repairs
stale release-evidence navigation, and corrects manifest metadata examples for
secret-bearing input. It retains `mammoth-io>=0.7.3,<0.8`, adds no API bindings
or API request-execution path, and makes no capability-status or
autonomous-workflow qualification claim.

Published from deterministic local artifacts built from tag `cli-v2.0.5`
(source commit `2a62d1c`). PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `6f20d4329d5e2f1d879fc9a3c2c394c840e63f6e1994a312e1308470a069539c` |
| Source distribution | `f3b23b9c1efa68a096d8fd38484099af5293fed86c419e0d966d8169b7cddb95` |

## 2.0.4 / SDK 0.7.3

Published from deterministic local artifacts built from tag `cli-v2.0.4`
(source commit `6714f90`). This security maintenance release hardens the
explicit file-backed credential fallback on POSIX. Every file read, update,
and delete now rejects unsafe directory or file ownership and permissions,
symlinks, non-regular files, and file-entry replacement before parsing
secrets. It retains `mammoth-io>=0.7.3,<0.8`, makes no API-binding or
capability-status change, and does not qualify autonomous workflows or backend
behavior.

PyPI reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `e62246975d559246e079c04f118cbafb31678f05ecc1fc04ab7308eb139e89b3` |
| Source distribution | `eb893be416b7d0c3dfde089550d17068601f939bd506ceb5d64e607973fbd759` |

Focused credential tests (14), Ruff, mypy, lock validation, build, and Twine
metadata validation passed. A fresh Python 3.14 environment installed the
exact published wheel, passed `pip check`, reported version 2.0.4, and ran a
bundled schema command. These checks do not constitute a full-suite or CI run.

## 2.0.3 / SDK 0.7.3

This CLI-only documentation correction makes every `mammoth-cli` README link
absolute, so the package README rendered on PyPI reaches the repository guides,
reference, and bundled skill. It retains
`mammoth-io>=0.7.3,<0.8`, adds no API bindings, and makes no capability-status
or autonomous-workflow qualification claim.

## 2.0.2 / SDK 0.7.3

This CLI-only maintenance release updates the packaged agent skill, installation
guidance, and release-capability documentation. It keeps the published SDK
requirement at `mammoth-io>=0.7.3,<0.8` and does not add API bindings, promote
capability statuses, or qualify autonomous workflows. The 2.0.1 API evidence
below remains historical evidence for that published release. Its relative
README documentation links do not resolve in PyPI's package rendering; 2.0.3
corrects that presentation defect.

## 2.0.1 / SDK 0.7.3

Published from deterministic local artifacts built from annotated tag
`cli-v2.0.1` (source commit `9243430`). This maintenance release restores the
CLI static release gates and requires `mammoth-io>=0.7.3,<0.8` for the SDK
security release.

PyPI JSON metadata reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `001ed77409aa44f405f47694ba9af0ad66cfd69b937a4860c3855fa66abe966d` |
| Source distribution | `61ece65817b0769cab788ae7594fe8528b456ffad41c9780167d6cae2f956f73` |

The lockfile resolves published SDK `0.7.3` and its wheel/sdist hashes;
`poetry check --lock`, focused contracts, Ruff, and mypy passed before upload.
An independent no-cache public-PyPI Python 3.14 install passed dependency
checks, CLI/SDK version checks, NDJSON lifecycle framing, and bundled skill
list checks. These checks do not qualify all API operations, autonomous
workflows, or untested backend behavior.

## 2.0.0 / SDK 0.7.2

Published from deterministic local artifacts built from annotated tag
`cli-v2.0.0` (source commit `da626f8`). This is a breaking release for the
versioned NDJSON lifecycle framing. The CLI requires
`mammoth-io>=0.7.2,<0.8`; SDK `0.7.2` was published first.

PyPI JSON metadata reports the uploaded local artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `98b8bd291e3b5564f849a5e8889c6a0ea4682b171dde2d56fe5d21518a120cac` |
| Source distribution | `1aa833e1e1257bea1613754c0c0aaa9bc719035ad10dcbca4a69ef57324bed1d` |

The lockfile resolves the published SDK `0.7.2` wheel hash and passed
`poetry check --lock`. Focused output, schema/discovery, identity, workflow,
and installer-document contracts passed before upload. Exact-artifact and
independent public-PyPI Python 3.14 installs passed `pip check`, reported CLI
`2.0.0` and SDK `0.7.2`, and exercised NDJSON lifecycle framing plus bundled
skill install/list checks. These checks do not qualify all API operations,
autonomous workflows, or untested backend behavior.

## 1.1.12

Published from deterministic **local** artifacts built from immutable tag
`cli-v1.1.12` (commit `7d02afa`). This is a fail-closed contract correction:
`view update` rejects arbitrary raw patch data until the API publishes a typed
request contract. It does not claim support for arbitrary view patches.

The artifact bytes were reviewed before the authorized local Twine upload; they
are not CI-built artifacts. PyPI JSON metadata reports the same SHA-256
digests:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `135b3384742d66ca4168b5afc2762a9c2502263228d6ee1a45f38560abf81a2e` |
| Source distribution | `a8caf87591e02bb06b130e20b6eebe1d92ec8b65a31db528b52ab77ae20138af` |

Focused local prechecks passed for the selected view/dataset tests (162), four
B09 no-dispatch regressions, Ruff, mypy, lock, generated-document check, links,
and the bundled skill catalog. Vale reported zero errors and existing warnings.
The full non-live CLI suite was not run for this release, so this release makes
no full-suite-pass claim. GitHub Actions remain disabled repository-wide at the
user's request, so no CI artifact, workflow, GitHub release asset, or signing
claim applies.

A fresh isolated Python 3.14 install of the exact local wheel passed `pip
check`, `mammoth --version`, `schema get view.update`, and the installed B09
no-dispatch smoke (`unsupported_contract`, exit 2) with an empty home directory.
A fresh isolated Python 3.14 public-PyPI install passed the same `pip check`,
version, schema, and B09 smoke checks after Simple-index propagation. These
checks do not qualify autonomous workflows, dashboard runtime behavior, or all
API operations.

An isolated published-skill smoke used a literal, prevalidated temporary
`HOME`, `CODEX_HOME`, and `XDG_DATA_HOME`. `skill path` resolved all three
agent destinations beneath that temporary root; the first install wrote three
owned copies, the repeat reported all three as identical, and `skill list`
reported all copies present and intact. Sixty bundled catalog and recipe links
resolved. The smoke found that the 1.1.12 generated catalog described the
fail-closed B07/B09 patch commands as runnable; that documentation defect is
corrected only in unreleased 1.1.13 source and does not change 1.1.12 behavior.

## 1.1.11

Published from deterministic **local** artifacts built from immutable tag
`cli-v1.1.11` (commit `ab0f898`). The artifact bytes were reviewed before the
authorized local Twine upload; they are not CI-built artifacts. PyPI JSON
metadata reports the same SHA-256 digests:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `25a811dad8d843731d719f20948ffe7df85dfb16a89f4cea1d8999925b54c962` |
| Source distribution | `c5339664d5be43a27cd43c15414c5ef896fb0ae229fd135845aa1f96aa765a7e` |

Local prechecks passed for the lock, Ruff, mypy, generated-document check,
links, and Vale (zero errors). The full non-live CLI suite was explicitly
cancelled at the release owner's direction and is therefore unconfirmed; this
release makes no full-suite-pass claim. GitHub Actions were disabled
repository-wide at the user's request, so no release workflow, CI artifact,
GitHub release asset, or signing claim applies to this release.

A fresh isolated, no-cache Python 3.14 install from PyPI passed `pip check`,
`mammoth --version`, `schema get dataset.create`, and an installed bundled
`SKILL.md` resource check. These checks do not qualify autonomous ETL,
dashboard runtime behavior, or all API operations.

An additional isolated Python 3.14 probe exercised installed public
`mammoth-cli` 1.1.11 and `mammoth-io` 0.7.1 with mocked transports only. A
cross-origin `302` made one original-origin request and was not followed;
empty and partial multi-job responses timed out rather than reporting success;
and a mutation `502` or malformed `200` produced `outcome_unknown`. The probe
used no live service or credentials and is focused regression evidence, not a
full-suite result.

## 1.1.10

Published from the exact `dist` artifact downloaded from successful CI
build-and-verify job [`105174083438`](https://github.com/EdgeMetric/mammothsdk/actions/runs/35212798832/job/105174083438)
for tag `cli-v1.1.10` (commit `20430eb`). Trusted Publishing failed, so the
authorized local Twine fallback uploaded only those downloaded bytes. PyPI's
JSON metadata reports the same SHA-256 digests:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `7b31296f1d2227791533a76cee1eb32a29eda4a344b4650f7aa3a0be556ddf4c` |
| Source distribution | `cfd7cab3e4d11f1b261805d5fdd9b149e83df8dfcacf2e5aa6a8abe0bdfc977a` |

A fresh Python 3.14 install from PyPI passed `mammoth --version`,
`schema get dataset.create` (including the documented `weburl` path and CLI
wait policy), and a bundled-skill recipe check. The GitHub-release job was
skipped; no signed GitHub release, Sigstore bundle, or signing claim is made.
These checks do not qualify autonomous ETL, dashboard runtime behavior, or all
API operations.

## 1.1.9

Published from the exact distribution files downloaded from successful CI
build job [`105151237784`](https://github.com/EdgeMetric/mammothsdk/actions/runs/35205826645/job/105151237784).
Trusted Publishing again failed with `invalid-publisher`; the authorized local
Twine fallback uploaded only those downloaded bytes. The PyPI downloads match
the CI hashes exactly:

| Artifact | SHA-256 |
| --- | --- |
| Wheel | `b15822ee3bbd00b201c2c49292fec8a10b7cae36df60082f29f2919b6f89e86e` |
| Source distribution | `6b63b21b6d57a5697e8a186f4ad3eb2240182c61d1c95a3d78a0d8a7f315aa67` |

A fresh Python 3.12 PyPI install passed `mammoth --version`, `schema list`
(547 commands), `pip check`, project-scope Codex skill installation (60 files),
and typed `fill missing`/`duplicate` discovery. The matching GitHub release
ships SHA256SUMS, wheel/sdist, and installers, but is explicitly unsigned: no
Sigstore bundle or signing claim is made. These release checks do not qualify
autonomous ETL, dashboard runtime behavior, or all API operations.

Dashboard release evidence remains a backend boundary, not a CLI/SDK defect
claim. Against an owned disposable dataview, the current-engine blank-create
route returned HTTP 403 with the server's `AUTHORIZATION_ERROR` (`4RESO001`),
which establishes only that this credential/request was denied; it does not
identify the missing entitlement. The legacy create route returned HTTP 409
`DASHBOARD_LEGACY_CREATION_RETIRED` (`4DASH012`), so retrying that route or
changing its payload cannot create a dashboard. The documented source-list
route returned HTTP 500 with an empty response body, a known server-variance
boundary. The CLI preserved each status and server detail in its structured
error envelope; no permission bypass, retry, or readiness promotion follows.
The retained release-evidence archive is indexed in
[capability evidence](capability-evidence/README.md); it does not contain a
dashboard-specific fixture directory.

The immutable PyPI 1.1.9 description retains its pre-publication README
snapshot of **7 Partial / 521 Unassessed**. Read the canonical
[machine-readable matrix](release-capability-matrix.json) for current counts,
rather than that immutable package description.

## 1.1.8

Not published. Its CI full gate failed before artifact construction because a
Python 3.10-compatible evidence-script change was introduced after the local
lint check and triggered Ruff's Python-3.11-only `UP017` suggestion. The
1.1.9 follow-up keeps the compatibility behavior and suppresses that specific
non-applicable suggestion.

## 1.1.7

PyPI 1.1.7 was uploaded through the authorized local Twine fallback after the
trusted-publisher exchange failed with `invalid-publisher`. Its local upload
bytes did not match the later-downloaded CI artifact bytes, so it must not be
treated as CI-byte-identical. No GitHub release assets were created for 1.1.7.

The recorded hashes are:

| Artifact | PyPI/local upload | CI artifact |
| --- | --- | --- |
| Wheel | `1c27140eec8663adf4109bea9812d22226c47d0ce14d031e769e8073e6622c48` | `cf280cfc86f190b28dbed5173a96b67f2305d8da85b12c36930fcd7cc9bf43f2` |
| Source distribution | `5df4f4ecec839cf2ebd0be0507e09cb6c0a02f2db0fddfcc2c696f8c77a69bb0` | `1fe28c03a17abddeeb9750be38eff08b0a81d6638310c61c6b0adc9a8d095dcc` |

The 1.1.7 release CI build-and-verify job passed; Trusted Publishing failed
because PyPI has no matching publisher configuration. This is a provenance
correction, not an ETL qualification or a claim that all API operations are
verified.
