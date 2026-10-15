# Changelog

All notable changes to `mammoth-io` are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (mammoth-cli, command and capability discovery)

- Did you mean: an unknown command names the nearest commands, including a nested group (`mammoth pipeline` -> `mammoth view pipeline`), and points to `mammoth how` / `mammoth schema find` instead of `schema get`; `details.did_you_mean` lists them and `recovery_commands` are ready to run. An unknown option names the nearest valid one (`--profle` -> `--profile`), and an option passed with its value as one argument (`"--project 3633"`, `--project3633`) says to pass the value separately. An unknown or wrong-case column (`Day` for `day`) names the closest column in the message, hint and `details.did_you_mean`.
- Allowed values in `--help` and in the error hint: an enum input field lists every value (it was cut at six, so `extract-date`'s `component` and `window`'s `function` hid most of theirs), and a fixed list inside a field gets an "Allowed values" line: `view transform batch` names its `steps[].op` list, and `dataset create` its `query_properties.data_pull_file` values. A refused batch op lists the allowed ops in `hint` (it was null) with `details.allowed` and `details.did_you_mean`. The help line, the hint and the check read the same tuple, so they cannot drift.
- `mammoth how "GOAL"`: turns a plain-language goal into an ordered recipe of commands. Each step has `command`, `command_id`, `purpose`, a runnable `example` (filled in with `--project` and an explicit `--profile`) and `key_flags`. Recipes cover refreshing on a schedule, appending a new file, blending two files on a key, upload to dashboard, a stuck upload, Power BI, CSV download, cleaning, sharing a dashboard and safe cleanup; they ship as `mammoth_cli/discovery/recipes.json`. A goal no recipe covers returns the `schema find` matches as steps with `matched: false` and a hint that says so. The bundled skill now starts with `how`.
- `mammoth capabilities` (also `mammoth schema find --unsupported [WORDS]`): what the CLI cannot do yet and what to do instead. Each entry has `area`, `limitation`, `instead`, `workarounds` (command and a runnable example) and `doc`. It lists file datasets that no automation can refresh, `schedule list`, editing a pipeline task through MCP (`view task update`), multi-project tokens and workbook imports built on synthetic data. The list ships as `mammoth_cli/discovery/limitations.json`; a test checks that every workaround is a real command.
- `mammoth skill show -o plain` (and `-o text`, a new alias of `plain` for every command) prints the skill file's markdown as it is, not one escaped JSON string; a terminal table prints it the same way. `-o json` is unchanged. The bundled `SKILL.md` front-matter `version` (it said 2.2.16) is stamped with the CLI version by `scripts/build_skill_catalog.py`, `skill show` stamps the running version, and a test keeps the two equal.
- `meta.next_commands`: after a main-flow command succeeds, one to three ready-to-run commands filled in with the result's ids: `file upload` -> `view data get VIEW_ID DATASET_ID` (or the dataset's own recovery command when it needs input), `view create` and every `view transform` -> `view data get`, `dataset file-settings update` -> `job wait`, `dashboard v3 generate` -> `dashboard get` and `dashboard figure add`, `dashboard figure add` / `figure-intent` / `chat edit` -> `dashboard get`, `automation create` -> `automation get`. Human output prints them as one `Next:` line on stderr. A write whose `verify` failed or is partial gets none. The map is `mammoth_cli/discovery/next_commands.json`.
- `dashboard figure add` accepts `{"intent": "..."}` (optional `kind`), as the bundled skill says: it goes through the figure-intent route, where the server picks and draws the chart, and the result carries `route: "figure-intent"`. An exact `figure` with `dataview_id` works as before. Passing both, or neither, is a usage error whose hint shows both shapes and names `dashboard figure-intent`.

### Fixed (mammoth-cli 2.2.86, team bug bash 2026-10-15)

- `dataset list` (and the name search) report a real `dataset_health` for every dataset. The list route already returns `status`; the compact summary dropped it for a ready dataset, so every row read `unknown` with a "run mammoth dataset get" hint. Each row now carries `status` (about 18 characters a row); no extra request is made, so big projects list as fast as before.
- `file upload`: the `dataset_health` entry carries the dataset's `name` (it was `null`), and each uploaded dataset in `datasets` has a `name`.
- Workspaces and projects are named beside their ids: `auth login` says "Signed in to workspace Filipe Silva (519), project Sales (4460)" and adds `workspace_name` / `project_name`; `auth status --check` adds `workspace_name` and `token_project_name`; the "token is limited to project" errors and the `project list` / `project get` notes name the pinned project. A failed name lookup falls back to the id and never fails the command.
- `auth status` (and `auth login`): `expires_at` is the access token's expiry, not the login's. It is kept, and `access_token_expires_at`, `refreshes_automatically: true` and `expires_at_note` say what it means. Documented in the bundled skill (`machine-output`, `auth`) and `docs/authentication.md`.
- Discovery: `schema find` ranks `folder.*` for "folder", "create/make/rename a folder" and "move a dataset into a folder", `file upload-folder` for "upload a folder of files", and `dataset delete` beside `file delete` for "delete an uploaded file". `mammoth --help` now says what `file` and `folder` are for (a folder is a project folder; an uploaded file becomes a dataset).

### Fixed (mammoth-cli 2.2.85)

- `file_exists` (exit 6, the global `--overwrite` from 2.2.82): the suggested recovery command keeps the `--project` and `--profile` you ran the command with (a profile that only the saved selection supplied is not pinned), and quotes `--input`. Before, it dropped them, so the re-run could land in another project or profile.
- `automation list` never shows a deleted or trashed automation. The server already leaves them out (a permanent delete removes the row; the trash filter hides `trashed_at` rows from every list), and the CLI now also drops any record that still carries `trashed_at` or a `deleted`/`trashed` status. This closes #31, the list half of the 2.2.82 delete check.
- Tests only: the two `test_prompt_cancel` Ctrl-C cases no longer time out when the suite runs detached (a background job starts with SIGINT ignored, and the child inherited that); the child now restores the default.
- `docs/llms-full.txt` and `docs/full-documentation.md` are regenerated from the current sources. The generator no longer prints Python's own `str` methods under every `str`-based enum.

### Changed (mammoth-cli 2.2.84)

- The bundled agent skill's `machine-output` reference describes 2.2.82's output: exit code 3 (partial), `status: failed` / `pending`, `file_exists` (exit 6) and the 0-based `paging` block with ready-to-run `next_command` / `previous_command`.
- Requires mammoth-io 0.8.43, which reports its own version correctly.

### Fixed (mammoth-io 0.8.43)

- `mammoth.__version__` matches the published version again: mammoth-io 0.8.40 to 0.8.42 reported `0.8.39`.

### Fixed (mammoth-cli 2.2.83)

- `dataset delete` no longer reports `api_error` (exit 1) after a delete that worked: the dataset get route answers `400 4DSET001` for a deleted dataset, and the post-delete check now reads that as gone.

### Changed (mammoth-cli 2.2.82, behavior changes)

- Exit code 3 is now used: a write whose read-back says only part of it took effect (`verify.outcome` `partial`) prints its envelope with top-level `status: partial` and exits 3. A write that did not verify (`verify.outcome` `failed`) now prints `status: failed` (the earlier word is kept in `verify.reported_status`) and exits 1, where it used to say `done` and exit 0 (for example `dashboard chat edit`). A write still running when the wait ends reports `status: pending` with `verify.next_command` (`mammoth view pipeline wait VIEW_ID`, or `mammoth job wait ID` for an automation) and keeps exit 0: it was accepted and must not be replayed.
- `view data get`, `view export list` and `view pipeline items` page with one 0-based block: `offset` is the number of rows to skip (`offset: 0` is the first page, and it is accepted), the response reports the `limit` and `offset` that were actually used, and `next` / `previous` are ready-to-run commands (null when there is no such page). Scripts that passed 1 for the first page must pass 0.
- Commands that write a local file (`view export csv`, `dashboard bi-export`, `explore-panel export-image`, `support template export`) refuse an existing file with `file_exists` (exit 6) unless `--overwrite` is passed.
- One confirmation rule: a delete, remove, clear or discard of something that cannot be undone asks for `--yes` (or a prompt in a terminal); `--confirm TARGET` is checked before any API call. `project memory remove`, `agent projects clear` and `agent plan discard` now ask; `dashboard tags rename` no longer does. Every runnable example from `schema get` carries the `--yes` / `--confirm` its policy requires.
- Data-app commands and `schedule create` fail at once with `feature_unavailable` (and no request) because the server does not offer them yet; they are hidden from `schema find`.
- String fields with a fixed vocabulary (snippet language, parameter type, annotation target type, project access, roles, and others) publish an `enum` in `schema get`, accept any letter case, and fail locally with the accepted list and a did-you-mean.
- An unexpected CLI fault is reported as `internal_error` (not `api_error`); `--debug` prints the traceback and the run log keeps the exception.
- Auto-update runs only in an interactive session (not in CI, not without a terminal).

### Changed (mammoth-cli 2.2.82, speed)

- `schema find` is about 30% faster: the operations manifest is cached and pydantic is imported only when a type is validated.
- `view get` makes one round trip instead of two.
- `view data get` makes 5 requests instead of 6; the dataview and the dataset are read concurrently.

### Added (mammoth-cli 2.2.82)

- `schema find` answers new-user phrasings with the right command, and marks partial matches instead of returning nothing.
- `schema get` examples are runnable for every command: distinct ids, real enum values, no `sample` placeholders, a lookup that names its target column, and a `--yes` where required.
- Preconditions (`known_restrictions`) for the 36 destructive and high-impact commands that had none; `schema get` no longer shows internal stub text.
- `view transform extract-date`, `date-diff`, `increment-date` and `math` check column types locally: a TEXT column is refused with `column_type_mismatch` and the `convert-type` command to run first.
- `dataset list` / `dataset health` report health from the fields the server sent, with a `health_reason`, instead of `unknown`; the name is filled after a file upload; `dataset file-settings update` waits for the reprocess job.
- A token limited to one project: `project list` shows only that project (with a note) and `project get OTHER_ID` is refused locally with `authorization_required`; a 403 hint blames a project-limited token only when the token is limited.
- `view transform generate-sql` returns an `apply` command that is runnable as printed (the view bound as `"view:ID"`, `--project` included).
- `parameter create` checks the name locally (`[A-Za-z_][A-Za-z0-9_]*`) and `schema get` publishes the pattern.
- `dashboard import-workbook` and `assess-twb` / `assess-pbix` wait for their job and surface rejected files; `dashboard bi-export` lists dropped figures.

### Fixed (mammoth-cli 2.2.82)

- `--output yaml` no longer crashes on data rows, schema documents or revealed secrets.
- `dashboard canvas save`, `figure add`, `pages add` and v3 generate no longer report a failed or swapped chart as verified.
- A delete the server accepts but does not carry out is an error, not a verified success; `automation delete` is verified by reading the automation (not found means gone), not by an empty list.
- `view transform add-sql` whose read-back fails after the step was stored is confirmed from the task list and reported done with a warning; an export that is no longer runnable after a pipeline change is flagged as stale.
- A bad condition operator and the failing step of a batch input are named in the error.
- An error message no longer carries terminal escape sequences; the duplicate-export refusal names the `save_as_mode` you asked for; a running automation is waited on with `job wait`, not "read the view".

- A pinned install is no longer replaced by the daily auto-update. `mammoth upgrade --version X.Y.Z` and `mammoth-install.sh` / `mammoth-install.ps1 --version X.Y.Z` record the pin (`pin.json` next to `update-check.json`; the installers call the hidden `mammoth upgrade --record-pin`, and a failure to record only warns); a plain `mammoth upgrade` or an installer run without `--version` clears it. While pinned, `meta.update_available` still shows the newer release but nothing is installed.
- `mammoth doctor` recommends `mammoth auth login` (with `--profile NAME`) when stored credentials exist but the login expired (`login_expired`, `not_authenticated`), instead of an empty `recommendations`.
- `mammoth doctor` reports `oauth sign-in present` for a browser login instead of `api token present`.
- Recovery commands and hints for `not_authenticated`, `login_expired`, a failed sign-in, `profile_not_found`, and the auth errors mapped from the API now carry `--profile NAME` for a non-default profile, so the suggested command signs in the profile that failed instead of `default`. Output for the default profile is unchanged.
- `mammoth --output xml project list` (a global option before the command, with a value the command rejects) returns the same JSON `usage_error` envelope as `--profile` when piped, instead of plain `Error:` text.
- Dashboard review and the upload `before_dashboard` hint no longer suggest `revenue = Unit Price * Unit Price`: a unit price or money column is never taken as the quantity. When the only quantity-like column is not NUMERIC (for example a `Quantity` with an `N/A` value), the hint says to convert it to NUMERIC first and offers no math fix.

### Fixed (mammoth-cli 2.2.81)

- `mammoth auth logout` treats a 401/404 from the server as the sign-in already being ended and signs out locally instead of failing.
- `mammoth auth login` warns when it replaced another profile's sign-in that shared the same Mammoth sign-in.

### Fixed (mammoth-cli 2.2.80)

- `mammoth auth login` with no terminal (`--no-input`, a pipe, `--output json`): the `login_input_required` error now names `--device` and `--method oauth --no-browser` as well as `--input`, and carries `recovery_commands: ["mammoth auth login --device"]`.
- `mammoth auth login --help` no longer prints `api_token*` as if every login needs it: the line reads `Input fields (--method token only; --device and --method oauth take none)`.
- Agents may run `mammoth auth login --device` themselves and show the user the link and code it prints (steering block, bundled skill, `docs/agent-prompt.md`, README). Browser and token logins stay with the operator.
- `mammoth project create` and `project ensure` ask `GET /workspaces/current` first and refuse with `authorization_required` before creating anything when the token is limited to one project, naming that project. `mammoth doctor` reports it as the `token_scope` check (`pinned_project_id`); `mammoth auth status --check` reports `token_project`.
- Dashboard review: the `unit_price_summed` finding points at the revenue/amount/sales column the view already has instead of suggesting a new `revenue` column.
- Release workflows (`cli-release.yml`, `sdk-release.yml`) run `python scripts/sync_openapi.py --check-served`, which fails when an operation the CLI or SDK calls is not served by production (extra production routes do not fail it; `--check-live` still does and stays manual).

### Fixed (mammoth-cli 2.2.79)

- `mammoth view transform batch`: a `limit-rows` step after a `sort` step now carries that sort's `order_by`, so the rows kept are the first N in the sort order instead of the first N in the table's own order.

### Added (mammoth-io 0.8.42, mammoth-cli 2.2.78)

- `mammoth view transform batch VIEW --input '{"steps": [{"op": "filter", "input": {...}}, ...], "dataset_id": N}'` adds several transforms in one request, so the pipeline runs once after the last step instead of once per step. Ops: filter, sort, limit-rows, discard-duplicates, fill-missing, bulk-replace, replace, text, substring, extract-date, increment-date, copy-columns. `sort` is applied after the run as a view setting. If a step fails, the batch's tasks are removed and the command fails with `batch_step_failed`, naming the step.
- SDK: `View.add_tasks(task_specs)` and `PipelineAPI.add_task` take a list of task specs and send them as one POST.
- SDK: `ExportStatus.QUEUED`.
- `mammoth agent chat` no longer fails with 400 `4GENR007` ("request_key: Field required"). The SDK makes the `request_key` for each submit and repeats it on its own retries after a gateway error; it is never part of `--input`. `agent chat` waits (default 120 seconds, `"wait": 0` to return at once) and returns the reply, or `working: true` with the `session_id` to follow with `agent session messages`. The `scope` shape (`{"type": "workspace", "workspace_id": N}`) and `client_context.project_id` are documented.
- `mammoth agent plan approve SESSION_ID`, `agent plan skip SESSION_ID N` and `agent plan discard SESSION_ID` do what the web app's Run it, Skip and Discard buttons do (typing "Run it" as a chat message approves nothing). The plan id is read from the session. `agent session messages` reports `awaiting_plan_approval` with the exact commands when a plan waits.
- `mammoth connector connection query CONNECTOR CONNECTION --input '{"query": "SELECT ..."}'` runs one SELECT and returns sample rows. It is read-only on the Mammoth side: no data source is saved and no dataset is made (only the short-lived job that carries the request), so it needs no `--yes`. The CLI refuses anything but a single SELECT; the connection's database user decides what the database allows.
- `mammoth connector connection list` works without a connector key and lists the connections of every active connector, each row with its `connector_key` (secrets stay redacted).
- `mammoth context show` prints the profile, endpoint, workspace and project the next command would use (never credentials).
- `mammoth schema get COMMAND --full` (the `--input '{"full": true}'` form still works).
- The recipes and `dataset create` preconditions cover importing from a REST API and from a database query; `schema find` ("rest api connector", "create dataset from a database query") now reaches `dataset create`. Stacking two datasets is documented as `view export dataset` with `save_as_mode` `APPEND_TO_DS`, including the refresh caveat; a real union step needs backend work.

### Changed (mammoth-io 0.8.42, mammoth-cli 2.2.78)

- A database export (`view export postgres` and the other database targets) returns after the export has run, with its status, error and run time, instead of when the export was added. A failed run fails the command with `export_failed`. `mammoth job wait` on the job that added such an export reports the same outcome. An export that is still queued counts as running; one that has not started after the wait is reported as scheduled.
- Pipeline waits ask first after 0.5 s instead of 3 s (`PipelineAPI.wait_for_pipeline` `poll_interval` default), and the CLI no longer polls the pipeline again after the SDK already saw it ready. Short transforms return several seconds sooner.
- `mammoth batch update` works again: the server takes one patch operation (`{"op": "replace", "path": "batches", "value": {"suspend": [ids], "restore": [ids]}}`), which the SDK and CLI now send as such (a list holding one operation is still accepted).
- `mammoth dataset bulk-delete` checks that every dataset is gone and fails, naming the ones still present, instead of exiting 0 after a partial delete.
- `mammoth view transform ai` fails with `task_runtime_error` (and the command that removes the task) when the AI step errors as it runs, instead of exiting 0 with an empty column.
- `mammoth project create` fails loudly, with the new project id, when the token that made the project cannot open it (a token limited to one project).
- The CLI updates itself with no prompt, at most once a day. After a command has written its output, a detached process asks PyPI and installs a newer release through the `mammoth upgrade` path. It never blocks or fails a command, logs failures to the run log, and never runs during `upgrade`. `MAMMOTH_NO_AUTO_UPDATE=1` keeps the check but never installs. It runs after the command because replacing files under a running command breaks its lazy imports. `meta.update_available` now appears only when a newer release exists and will not be installed by itself.
- `view create` reports `view_id` and `dataset_id` with a short summary instead of the full dataview record (`view get` has it).
- `view list` lists views that do not fit in full by id and name, so the output cap hides far fewer of them; the more/offset hint stays when views are really cut.
- `dataset create` waits briefly for the new dataset's default view when it reads the result back, instead of reporting `unreadable`.
- `view data aggregate` adds `currency_note` only when a measure reads as money.
- `mammoth doctor` prints the exact `mammoth auth login --profile NAME` command for a legacy API key + secret profile.
- Preconditions shown by `schema get` no longer carry internal test-harness text (fixture requirements, evidence provenance, variance codes).

### Fixed (mammoth-mcp-server 0.2.2)

- A read-only connection that calls a change tool now gets the refusal as a tool result the model can read ("This connection is read-only, so <tool> cannot run…"). Before, the refusal reached the client as a protocol error, and Claude Code showed it as "Internal server error". The write was refused either way.

### Added (mammoth-mcp-server 0.2.1, mammoth-io 0.8.39)

- `client.workspaces.current()` says whether the user granted the connection read-only (`CurrentWorkspace.read_only`, false when Mammoth does not say). The MCP server puts the `read` scope on such a token, so the read-only check added in 0.2.0 now applies to the connections Mammoth marks read-only. Needs a Mammoth that reports `read_only` on `/workspaces/current`; with an older one every connection keeps full access.

### Added (mammoth-mcp-server 0.2.0)

- A connection reads only the workspace its token belongs to. `list_workspaces` listed the whole account, so a connection fenced to one workspace was told the names of all the others.
- Every tool carries a title, which is what a client shows the user when it asks them to allow a call.
- One telemetry event per handshake and per tool call (tool, client, duration, outcome), and never the arguments a tool was called with. Each event is written to stdout and stored in Mammoth's user events as the caller's own, so Mammoth can count tool calls per user.
- A read-only connection may run only the tools whose own annotation says they read. No token carries the scope yet, so nothing changes for an existing connection.

### Changed (mammoth-cli 2.2.75)

- CLI capability gaps (PR #215): OAuth login uses a login-server prefix and network retry in the device flow, and Ctrl-C/EOF at prompts is handled again. Requires mammoth-io >=0.8.39.

### Fixed (mammoth-io 0.8.38)

- `mammoth.__version__` now matches the published version. 0.8.37 shipped with `__version__` still at 0.8.36, so it reports itself as `mammoth-io/0.8.36` in the `User-Agent` header. Use 0.8.38.

### Added (mammoth-io 0.8.37)

- `MammothClient(user_agent=...)` places a caller's product token (for example `mammoth-cli/2.2.72`) before `mammoth-io/<version>` in the `User-Agent` header, so a tool built on the SDK no longer rewrites `client.session.headers`.

### Changed (mammoth-cli 2.2.74)

- An explicit `--profile` now wins over `MAMMOTH_API_TOKEN`; an env token alone prints a stderr note, `view data` reports `paging.total` only when no sequence is given, and the CLI sends `mammoth-cli/<version>` through `MammothClient(user_agent=)` (needs mammoth-io >=0.8.38).

### Added (mammoth-cli 2.2.73)

- REST API import recipe (connection, ds-config sample, dataset with scheduled refresh, Elasticsearch notes); `schema find` routes REST/API import phrasings; `ds-config create` help names the query shape; scheduling `start_at` rules and dashboard limits documented.

### Changed (mammoth-cli 2.2.72)

- The CLI signs in with the built-in `mammoth-cli` OAuth client when the server publishes none; the per-environment client table is gone, and the login menu always offers Browser and Device.

### Fixed (mammoth-io 0.8.36)

- The transport log redacts the path segment after `clientapps`, so an app key no longer reaches the log line or its structured `path` field.

### Fixed (mammoth-io 0.8.35, mammoth-mcp-server 0.1.1)

- `CurrentWorkspace.project` carries the one project a credential may act in, so the MCP server reads the connection's pinned project instead of asking the user for one it was already given.
- `list_projects` asks for a pinned connection's project by id. It used to filter one page of the workspace's projects, which answered "no projects" whenever the pinned one sat on another page.
- `check_upload` waits for Mammoth to take the file instead of ending the model's turn on the upload link.
- An upload Mammoth refuses relays Mammoth's own status and words rather than a bare failure.

### Changed (mammoth-io 0.8.33, mammoth-cli 2.2.71)

- Browser and device sign-in read the CLI's OAuth client id from the server's OAuth metadata (`mammoth_cli_client_id`) and fall back to the built-in table when the server does not publish it.
- mammoth-io gains `mammoth.oauth.metadata_request`, the OAuth metadata GET the CLI uses, so the CLI keeps no HTTP client of its own.
- mammoth-cli upgrades itself by default in a terminal (not when stdout is piped or `CI` is set); `MAMMOTH_AUTO_UPGRADE=0` turns it off and `MAMMOTH_AUTO_UPGRADE=1` forces it on. The update check runs hourly instead of daily, the update hint names the off switch, and `mammoth upgrade` reports `installed_version`, the version a fresh interpreter prints after the upgrade.

### Fixed (mammoth-io 0.8.32, mammoth-cli 2.2.70)

- `mammoth doctor` exits 4 when its report says `ok: false` (the report is still printed).
- mammoth-io retries a read that got HTTP 429, waiting for `Retry-After` (capped at 5 seconds), twice.
- `MammothAuthError` keeps the server's `error_code` and `hint`, and the CLI shows them instead of the generic sign-in advice.
- The README names the hosted MCP server (https://mcp.mammoth.io/mcp) and `pip install mammoth-mcp-server` (needs `MCP_ENCRYPTION_KEY`) instead of `mammoth-mcp`.
- mammoth-mcp-server answers the browser CORS preflight on `/mcp` without a token.
- Browser and device sign-in are available on the production app (`app`): the CLI now carries its OAuth client id there, and the login menu no longer says "not yet available on app".

### Fixed (mammoth-cli 2.2.69)

- Unknown flags are named: an unrecognised option is reported as `unknown_option` with the flag in the message (#179).

### Fixed (mammoth-cli 2.2.68)

- `connector get` reports plan availability like `connector list`, so an included connector is no longer read as a paid one (ISS-263).
- `connector connection list` without a key tells the caller to run `mammoth connector active`.

### Fixed (mammoth-cli 2.2.67)

- A view read that goes async (`--return-running`) keeps its dataset and view meta in the running envelope.
- The error-summary AST scan no longer false-positives on `_backend_message`'s local (renamed to `backend_code`).

### Fixed (mammoth-cli 2.2.66)

- `dataset find` names the in-project exact match instead of telling the caller to ask; the elsewhere note says the in-project match is the answer and other projects matter only when the user names one.

### Fixed (mammoth-cli 2.2.65)

- `dataset find` (and the name fallback of `dataset list`) reads one workspace search instead of every holding project's dataset list, which took 20+ s for a project of a few hundred datasets.
- Data reads on a view carry the row count of the view and of its dataset (ISS-244).

### Fixed (mammoth-cli 2.2.64)

- `dataset create` raises `job_failed` when a waited create job settled without a dataset; a cloud import deferred to a later start reports `scheduled`, and `datasource_id` counts as the dataset id.
- A cloud file create with `file_path` and no `data_pull_file` defaults to "Pull same file"; a bad pull mode lists the allowed values.

### Added (mammoth-cli 2.2.61)

- `mammoth agent projects clear AGENT_KEY` empties an agent's project list (`projects set` cannot: `*_ids` lists need one item).
- Table mode shows the backend's own message (and code) on a 4xx, one line per field for validation errors; `agent roles` prints a table.

### Fixed (mammoth-cli 2.2.63)

- `connector list` uses the server's `is_available` instead of inferring availability from `is_premium` and `is_added`.
- Under `--project`, `resolve` and `dataset find` return only the project's own rows when one matches the name exactly; `elsewhere` counts the rest, and `--input '{"all_projects": true}'` lists all.

### Fixed (mammoth-cli 2.2.62)

- The agent no longer invents a name for a new dataset (QA ISS-195: "Branch out View 1 of X into a new dataset" produced "X - View 1 branch" instead of "Result Dataset"). The bundled skill's new-dataset examples (`view export dataset`, the cross-project send recipe, the in-place-edit recipe in `schema`) omit `dataset_name`, and SKILL.md states the rule: pass it only when the user named the dataset; omitted it is "Result Dataset", as in the app. Appending to an existing dataset (`target_ds_id`) is unchanged. `view transform crosstab` still requires `dataset_name`.

### Fixed (mammoth-cli 2.2.60)

- A folder has one id in CLI output: the resource id the web app opens it by (QA RS-12: the agent showed a folder under its label id and its receipt under its resource id, two cards and a broken link). `folder create/get/list/update/find` and every folder in `browse project/folder/root/workspace/resources/resource/search/ancestors` print that id as `id`; the separate `resource_id` field, the label id, and the label ids in `parent_id` and `resource_path` are gone. `folder get/update/delete/trash/bulk-delete`, `folder list` `folder_ids`, a `folder move` target, `browse folder`, and `browse resource label` take that id. The old label id is no longer accepted (the feature is unshipped). `folder create --input parent_resource_id` is unchanged.

### Added (mammoth-io 0.8.31, mammoth-cli 2.2.59)

- Agent definitions: `client.agent_definitions` (SDK) and `mammoth agent create|get|list|update|delete|publish|disable|roles`, `agent charter get|set|versions|restore`, `agent access set`, `agent projects set`, `agent team set`, `agent goldens add|list|remove|run|status`, `agent memory add|list|remove`, `agent scratch set|get|list|clear` and `agent feedback list` build, prove and publish a workspace agent. The set commands take their values from `--input` (for example `agent access set KEY --input '{"role": "member", "propose": true}'`). The CLI requires `mammoth-io>=0.8.31`; the server routes ship with the matching mvc-service release.
- The bundled skill carries a recipe for building, proving and publishing an agent (`references/recipes/build-an-agent.md`).
- Every non-read command that calls the API now names its operationIds in its manifest; a contract test fails when one is empty, apart from commands that make no HTTP call.

### Added (mammoth-cli 2.2.58)

- `--standing` stages a step that changes no row today as a rule for future data: `view transform filter` on a column with no blank (QA R-5, "keep only rows where region is not empty") used to be refused as `no_op` / `no_change`. With the flag a dry run reports `predicted_impact` with `standing: true` and 0 rows removed, and a real run adds the step and says `standing_rule.removed_now: 0`. Without it the `no_op` error and the `no_change` result now name the flag in their `hint`. The flag applies to every step behind the same row-count gate: `filter`, `discard-duplicates`, `replace`, `bulk-replace`, `fill-missing`.

### Fixed (mammoth-cli 2.2.57)

- `folder create` now reads the new folder back: its `readback` named `result.folder.id`, but the command returns the folder flat (`result.id`), so the `state` block was `unreadable` and callers got no folder id receipt. The id now resolves from `result.id`.

### Changed (mammoth-io 0.8.30, mammoth-cli 2.2.56)

- 2.2.55 shipped without #173 (PyPI is immutable); 2.2.56 adds it: `view export dataset` dataset name is optional (default "Result Dataset").
- Adds `view export live-link` (#169), explore-panel real cards (#167), draft-write fixes (#170), start-up perf (#171) and prompt-cancel/login fixes (#172). The CLI now requires `mammoth-io>=0.8.30`.

### Changed (mammoth-io 0.8.28, mammoth-cli 2.2.54)

- Combined CLI fixes from #163 (see the entries below). The CLI now requires `mammoth-io>=0.8.28`.

### Changed (mammoth-io, mammoth-cli)

- Start-up is much faster. `mammoth --version` no longer builds the command tree, root `--help` and a mistyped command no longer build all ~550 commands, and the SDK package, its API sub-clients and its models load on first use instead of at `import mammoth`. A daily PyPI check now runs in a detached process instead of holding the finished command open for up to 3 seconds.
- A command group's `--help` (for example `mammoth view --help`) no longer imports every command's handler module and the SDK models: each command builds its parameters when it is first used, and the listing reads its summaries from `mammoth_cli/commands/help_summaries.json` (regenerate with `python scripts/gen_help_summaries.py`; a unit test fails on drift). The help text is unchanged.
- Start-up round 2: command modules and handlers are imported per command, only when that command runs, so `--help` and typo suggestions import none of them; the OS keyring backend is remembered after the first run instead of re-detected (~0.3 s) on every run that reads a keyring credential.

### Added (mammoth-cli 2.2.53)

- A TEXT column with blank cells now carries `fill_template` in its `blank_values` warning: a `view transform set-values` command with a `<value>` placeholder. The agent offers the fill, asks the user for the value and never runs the template as is; `fix` is unchanged.

### Fixed (mammoth-cli 2.2.52)

- The auth-failed hint now also covers expired or revoked OAuth sign-ins (`mammoth auth login`), not only API tokens.

### Fixed (mammoth-cli 2.2.51)

- OAuth login adopts the project the grant is pinned to, instead of keeping a different saved default project.

### Fixed (mammoth-cli 2.2.50)

- The fix commands in `column_warnings` (convert-type, bulk-replace, discard-duplicates, filter) now include `--project <id>`. Run from a profile with another default project, or inside the agent (no saved project), they failed.

### Added (mammoth-io 0.8.27, mammoth-cli 2.2.49)

- `mammoth view variants create` makes one filtered view per value of a column in one call (#152, #154). A null name template defaults, and an unreadable column list fails loud.
- `mammoth view explore-panel get|set` reads and writes a view's explore panel, and `mammoth dashboard figure add` appends a figure (#153). SDK: `explore_panel`, `set_explore_panel`, `append_figure`.

### Changed (mammoth-cli 2.2.49)

- The CLI now requires `mammoth-io>=0.8.27`.

### Added (mammoth-io 0.8.26, mammoth-cli 2.2.48)

- `mammoth auth login --device`: device-code sign-in (RFC 8628) for a machine with no browser. SDK: `mammoth.oauth.device_authorization_request`; `ClientAppPostResponse.expires_at`. API keys made by `mammoth token create` expire after 30 days. Needs the matching Mammoth server release.
- `mammoth view optimize VIEW_ID` takes one id: the dataset is read from the view. A DATASET_ID that is not the view's parent fails before any write, naming the real one.
- A copy job's result adds `derived_datasets: [{dataset_id, from_view_id}]` beside the old `derived` map.
- Dataset health and column warning `fix` hints are quoted and checked against the command manifest.

### Changed (mammoth-cli 2.2.48)

- A 403 hint says to check the ids and scope first; only a 401 session failure says to ask the user to sign in again.
- The CLI now requires `mammoth-io>=0.8.26`.

### Changed (mammoth-cli 2.2.47)

- A write's read-back waits for the new step's data and describes a staged draft step; a draft submit and a task delete or update are read back after their job finishes.
- A keep filter that no row matches fails its dry run and names the values its column holds; `--allow-empty` adds it anyway. A math step names the input columns that have blanks and is never blocked by a count that cannot run.
- A password-protected file in a result names the command that unlocks it and says to ask for the password.
- A backend NOT_ALLOWED refusal is an authorization error with the backend's reason. A retryable read's hint names the server's delay only when it gave one. A call from inside a running event loop runs the SDK work on a helper thread.
- The CLI now requires `mammoth-io>=0.8.25`.

### Added (mammoth-io 0.8.25)

- Public names for a server built on the SDK. `WorkspaceAPI.current()` returns the token's workspace
  and the `resource` (RFC 8707) an OAuth token was issued for. `MammothClient.set_workspace_id(...)`
  names the workspace a token client acts in, so it does not ask the API.
  `MammothClient.request_json(...)` calls a route the SDK has no method for. `mammoth.builders` holds
  the spec builders, `export_contract(...)` and `EXPORT_CONTRACTS`.

### Fixed (mammoth-io 0.8.24, mammoth-cli 2.2.46)

- `view data explore`: a blank bucket sorts last under `metric_*` and `count_*` orders too (it ranked by its own metric before).

### Added (unreleased: next mammoth-io and mammoth-cli)

- `mammoth auth login --device`: device-code sign-in (RFC 8628) for a machine with no browser. The
  CLI prints a short code and a URL, you approve on another device, and the CLI polls until you do.
  Needs the matching Mammoth server release.
- API keys made by `mammoth token create` now expire after 30 days. A command with an expired key
  stops with `cli_key_expired` and tells you to run `mammoth auth login`.
- SDK: `mammoth.oauth.device_authorization_request`; `ClientAppPostResponse.expires_at`.

### Added (mammoth-cli 2.2.45)

- `mammoth resolve NAME`: read-only, says whether a name is a dataset, a view or a project, with ids
  and projects, across every project the login can see.
- `mammoth dataset find` with `--project` now also returns matches in every other visible project,
  each marked `in_project`, so a name in another project is stated instead of asked about.

## [0.8.23]

### Changed

- `client_apps.create` no longer swallows a model mismatch silently: it still returns the created
  app and its one-time token, and also emits `MammothModelDriftWarning` naming the failing fields.
  `mammoth token create` prints that warning in the result's `warnings`.

## [0.8.22]

### Fixed

- `client_apps` models match apiv2: `list`/`get`/`update` read plain field values (not
  `{"value": ...}` wrappers), and `create` returns the flat response with the one-time `token`.
  Before, `token create` and `token list` failed model validation (QA W7-17) after the key was
  already created, so its secret was never shown.
- `client_apps.create` always sends `description` (empty when omitted), which apiv2 requires.
- `client_apps.create` returns the created app and its token even if the 2xx body drifts from the
  model, since the token cannot be fetched again.

## [0.8.21]

### Added

- `MammothClient(token_provider=...)`: a callable returning the current `mm_...` token, called for
  every request, so a short-lived token that is refreshed elsewhere is always sent fresh. Static
  `api_token` and `api_key` + `api_secret` clients are unchanged.

## mammoth-cli 2.2.42

- `mammoth token list` and `mammoth token create` on an API-token profile now say the call used an API
  token and that managing API keys needs `mammoth auth login` (browser sign-in), instead of claiming the
  server refuses CLI-created keys.

## mammoth-cli 2.2.41

- OAuth login works on the koyal dev server.

## mammoth-cli 2.2.40

- `mammoth auth login` offers a browser sign-in (OAuth, PKCE, loopback) next to pasting an API
  token; `--method oauth|token` and `--no-browser`. The session is a 1 h token that refreshes itself
  under a file lock. `auth status` shows the method and expiry; `auth logout` also revokes the
  connection on the server, and warns (still clearing local state) when it cannot.
- `mammoth token create / list / revoke` are aliases of `client-app create / list / delete`.

### Added

- `mammoth-cli` 2.2.40: reads return what the agent fetched next. `view list` adds `built_from`/`feeds`
  (view ids), `pipeline_status` and `in_sync`; `view analyze 5000,5001` takes several ids (up to 12) and
  returns `{requested, analyses, errors}` with each view's rows, columns, dataset and pipeline `steps`;
  `job wait` returns an `outcome` for a view run (rows, columns, status) and a `project copy`
  (datasets, views, skipped, and per-view `runs` when the backend records them). Independent reads
  now wait together (`call_many`) instead of in turn.
- `mammoth-cli` 2.2.40: `schema get` takes several command ids joined by commas or semicolons
  (`schema get view.list,view.analyze`) and returns one result, `{"requested", "schemas", "errors"}`;
  an id with no schema is an entry in `errors` and does not fail the call. `schema find` already took
  `;`-separated goals. Up to 12 ids per call (`too_many_ids` above that).

### Fixed

- `mammoth-cli` 2.2.39: `project copy` now says in its NAME help that a taken name is fine: the server names the
  copy with the next free suffix ("NAME 2", "NAME 3", ...), so an assistant no longer looks the name up or asks
  the user for another one.
- `mammoth-cli` 2.2.38: a file type the server refuses in `file upload` now fails with code
  `upload_refused` (still exit status 2) and the summary "Mammoth doesn't accept this kind of file, so
  nothing was uploaded.", instead of `invalid_argument`'s "request wasn't valid" framing.

## [0.8.20]

### Added

- `FilesAPI.upload_result(...)` returns `{"job_id", "dataset_ids", "errors", "nested_job_ids"}`, so a
  caller can see the files the server refused (`errors.unsupported_files`).

### Fixed

- `PipelineAPI.latest_task_sequence` skips `suspended` and `suspending` tasks as well as deleted ones,
  so `DataviewsAPI.get_data` no longer sends a sequence the server rejects with 404 4DTVW005.
- `FilesAPI.upload` raises `MammothValidationError` when the server refused the files and no dataset
  was created, instead of returning `None`.

## [0.8.19]

### Added

- `DataviewsAPI.analysis(dataset_id, dataview_id)` lists pipeline steps that can be dropped or moved
  without changing the result (read only); `DataviewsAPI.optimize(dataset_id, dataview_id,
  apply_rules=None)` applies the safe findings and reruns the view (a write);
  `DataviewsAPI.compare(pairs)` compares up to 20 dataview pairs: rows, column differences and
  checksums (read only).
- `DashboardsAPI.attachment_intent(attachment_id, target_dataview_id)` and
  `DashboardsAPI.attachment_assess(attachment_id)` queue the read of an attached workbook; both return
  `{"future_id": N}` to wait on.
- `ProjectsAPI.copy(project_id, name, dataset_ids=None, include_dashboards=False,
  exclude_data=False)` queues a project copy and returns `{"job_id": N}`.

### Changed

- `DashboardsAPI.duplicate` takes `project_id` and `target_dataview_id`. With a target view the copy is
  made in that view's project and the result carries `swap_job_id`.

## [0.8.17]

### Added

- `ProjectsAPI.delete_and_verify(project_id)` and `ProjectsAPI.bulk_delete_and_verify(project_ids)`
  delete, then poll the project list until every id is gone. The delete routes answer 202 with an
  empty body and no job id, so `delete` alone never says whether the project went. The result is
  `{"project_id": N, "status": "deleted", "verified": True, "ack": ...}`; on timeout (the client's
  job timeout) they raise `MammothDeletionVerificationError` naming the ids still listed.

## [0.8.16]

### Added

- `DatasetsAPI.search(term)` finds the project's datasets whose name, column names or sampled
  column values contain `term`, with the matched column and value (route
  `GET .../datasets/search`).

## [0.8.15]

### Fixed

- `ActivityLogsAPI.list` sent `limit`, `offset` and `sort` in the request body, but the route reads
  them from the query string: every page was the first page and `sort` was ignored. They now go
  as query parameters. New `fields` argument chooses the entry fields (the route's default carries
  every entry's full details).

## [0.8.14]

### Added

- `DataviewsAPI.explore(cumulative=True)` adds a `cumulative` running total per bucket (of the
  metric, else the count), in bucket order, before any sort or limit.

### Fixed

- `DatasetsAPI.list_all` no longer stops after the first page: the datasets list route sends no
  `next`, so a full page now continues until a short one (datasets past the 100th were invisible).
- `BrowseAPI.resources_search` / `resources_list` map the resource type `dataset` to the route's
  `datasource` (the backend rejected `dataset`).
- A `view.export.to_dataset` whose export trigger is slow to show `EXECUTED` resolves the new
  dataset by name and source view before giving up; the error it raises when it still cannot
  carries `export_pending: True`.

## [0.8.13]

### Fixed

- `AiAPI.get_data_gen_info` now sends `validate_only=true`, which the route requires.
- `DataviewsAPI.update` docstring example uses the server's patch path `name` (no leading slash).

## [0.8.12]

### Added

- API gaps closed (PR "build gaps 5"), each with a CLI command in `mammoth-cli` 2.2.11:
  - `DashboardsAPI.swap_fit`, `audience`, `audience_digest_get`, `audience_digest_set`,
    `audience_summary`, `column_roster`, `context_review`, `context_apply` and
    `qa_insights` (CLI: `dashboard swap-fit`, `dashboard audience get|summary`,
    `dashboard audience digest get|set`, `dashboard columns`, `dashboard context
    review|apply`, `dashboard qa insights`).
  - `AgentsAPI.turn_cancel` (CLI: `agent turn cancel`).
  - `DataviewsAPI.delete_impact` (CLI: `view impact`).
  - `BrowseAPI.resources_bulk` now has a command: `browse resources bulk`.

### Changed

- `addon list` and `user change-password` are retired in the CLI: the server no
  longer serves them, so they exit with a `not_available` error that names the web
  path. `AddonsAPI.list` and `UserProfileAPI.change_password` stay and are marked
  retired in their docstrings.

## [0.8.11]

### Changed

- Burst fixes (PR #90) so one CLI or SDK call no longer floods the API:
  - Lookups use the `/resources` routes instead of walking projects: a view's
    parent is one read (was 1 + D/100 + D requests), `dataset find`, `dataset
    list name` and `folder find` are one workspace search (was 2 + P or 1 + P),
    and name lookups use `BrowseAPI.resources_bulk`. A cross-project `view list`
    stops at 20 views or 25 datasets and says where to resume.
  - `view data profile`, `project check` and stored-stats reads use fewer
    workers (6 or 8 before, 2 or 4 now) and cap what they read: the 20 most
    recent datasets, 10 dashboards and the first 20 columns. The output says how
    many items were not checked.
  - Job waits back off: the poll gap ceiling rises from 2s to 5s after 10s of
    waiting (a 300s wait: about 154 polls before, about 70 now). Pipeline waits
    grow from 3s to 15s, and `view pipeline wait` defaults to 300s instead of an
    hour. Internal-dataset export polls grow from a flat 2s to 2..10s.
  - File upload polls the nested jobs once as a batch instead of one poll loop
    per file. The CLI previews the first 5 datasets and marks the rest
    `preview_skipped`.
  - `MammothClient(retry_gateway_errors=False)` turns off 502/503/504 read
    retries. The CLI sets it when embedded. `mammoth-cli` 2.2.10 carries these
    changes.

## [0.8.10]

### Fixed

- `json={}` request bodies are sent instead of dropped; `rename_columns` and
  `sort_rows` honour build-only mode; the export poll reads every page;
  `/resources/bulk` lookups are chunked at the server cap of 100; `list_users`
  and `get_user` page through all users; a pipeline dataset lookup that cannot
  resolve a dataset now raises `MammothAPIError` instead of skipping silently.
- `resolve_token_workspace_id` raises `MammothAPIError` on a non-JSON reply and
  bounds its cache. Dashboard and support downloads write files off the event
  loop. Embed secret fields are excluded from `repr`.
- Embedded-mode security and safety fixes (PR #87), and correctness fixes
  across `mammoth-cli` 2.2.9 (PR #86): complete folder, project and pipeline
  reads, exact-parent rule on pipeline and export writes, honest truncation and
  freshness flags, and refreshed lock files.

## [0.8.9]

### Added

- Platform-admin `SupportAPI` methods (each route refuses callers without a
  Mammoth staff role): `plan_unarchive`; `plan_storage_option_list`,
  `plan_storage_option_create`, `plan_storage_option_update` and
  `plan_storage_option_archive` for a plan's purchasable storage sizes; and the
  curated template catalog: `template_list`, `template_edit`,
  `template_data_preview`, `template_canvas`, `template_publish`,
  `template_unpublish`, `template_retire`, `template_inspect`,
  `template_import`, `template_thumbnail_set`, `template_thumbnail_clear`,
  `template_discard`, `template_snapshots`, `template_audit`,
  `template_export` and `template_export_dashboard`.
- CLI: `support plan unarchive`, `support plan storage-option list|create|update|archive`,
  `support template list|edit|data-preview|canvas|publish|unpublish|retire|inspect|import|discard|snapshots|audit|export|export-dashboard`
  and `support template thumbnail set|clear`. Each help line starts with
  "Platform admin only".

## [0.8.8]

### Added

- `BillingAPI.stripe_resume` keeps the paid plan by clearing a scheduled
  downgrade; `BillingAPI.stripe_recheck_limits` recomputes the over-limit lock;
  `BillingAPI.stripe_storage_update` sets the purchased storage (total GB).
- `BrowseAPI.resource_ancestors` reads a folder's path (root first);
  `BrowseAPI.resources_search` searches resources across the workspace.
- `DashboardsAPI.template_thumbnail_get`, `template_thumbnail_set` and
  `template_thumbnail_clear` read, replace and remove a template's picture;
  `DashboardsAPI.gallery_list` and `gallery_get` read the public template gallery.
- CLI: `billing stripe resume`, `billing stripe recheck-limits`,
  `billing stripe storage set`, `browse ancestors`, `browse search`,
  `dashboard template thumbnail get|set|clear`, `dashboard gallery list|get`.

## [0.8.7]

### Added

- `DashboardsAPI.embed_usage_summary` counts the active embed origins of several
  boards at once; `DashboardsAPI.format_preview` dry-runs a format switch.
- `WorkspacesAPI.home_summary` reads the Home summary (usage, health issues,
  suggestions).
- `BrowseAPI.resources_list` and `BrowseAPI.resource_get` read project
  resources through the v2 cursor routes.
- CLI: `dashboard embed usage summary`, `dashboard format-preview`,
  `workspace home`, `browse resources`, `browse resource`.

## [0.8.6]

### Changed

- Login sends the token alone: no workspace id goes with it. The workspace
  comes from the token (`resolve_token_workspace_id`).
- `except` clauses are parenthesised, so the package imports on Python 3.12
  and 3.13.

### Added

- `mammoth link`.
- `mammoth dataset broken-rows resolve` settles the unstructured rows of a
  file whose dataset stopped for a decision.
- `mammoth project needs-attention` also lists `needs_input` rows.
- `mammoth folder find` searches every project, not only the first page.

### Fixed

- A 403 for a user who is not a member of the workspace now says so.

## [0.8.0]

### Added

- GET and HEAD requests retry up to twice on a transient 502, 503 or 504, or a
  connect error (0.25 s, then 0.5 s; a numeric `Retry-After` is honoured, capped
  at 5 s). Writes are never retried.

### Changed — breaking

- The SDK is async. Every method that calls the API is a coroutine and must be
  awaited: `await client.views.get(1039)`, `await view.filter_rows(...)`,
  `await client.datasets.list()`. `View.is_draft_mode` is an async property:
  `await view.is_draft_mode`. Pure builders and setters stay sync
  (`client.set_project_id`, `Condition`, the spec models).
- The transport is `httpx` instead of `requests`, which is no longer a
  dependency. API calls still raise `MammothAPIError` for transport failures;
  only code that uses `client.session` or `client.download_session` directly
  sees the change — both are `httpx.AsyncClient`s now.
- `MammothClient` is an async context manager: `async with MammothClient(...)
  as client:`. `close()` is a coroutine. The sync `with` form is gone.
- One client belongs to one event loop: its connection pool lives on the loop
  that first used it.

Migrating from 0.7.x:

1. Run SDK calls inside a coroutine, e.g. `asyncio.run(main())`.
2. Put `await` in front of every call that reaches the API.
3. Replace `with MammothClient(...)` with `async with MammothClient(...)`, or
   call `await client.close()`.

Code that must stay sync should pin `mammoth-io<0.8`.

### Added

- `MammothClient(api_root=...)` addresses the API server directly, for a
  caller inside the network. The default stays `"/api/v2"`.
- `MammothClient(job_poll_seconds=...)` and a `poll_interval=` argument on the
  job waits (`JobsAPI.wait_for_job`, `JobsAPI.wait_for_jobs`,
  `MammothClient.wait_if_job`, `PipelineAPI.wait_for_pipeline` and the data
  reads that wait) set how often a running job is asked. Default:
  `DEFAULT_JOB_POLL_SECONDS`.
- `fields=`, `limit=` and `offset=` on `BrowseAPI.workspaces` and `projects`
  ask for one page of smaller records.
- `PipelineAPI.preview_task(sample_size=...)`.
- `DashboardsAPI.generate_v3` builds a v3 dashboard. `DashboardsAPI.action`
  takes `params_sequence` (restore a version) and `params_filter_column`
  (row-level security).
- `DatasetsAPI.preview_interpretation`, `confirm_interpretation` and
  `resolve_unstructured_rows`, for a file whose dataset stopped for a decision.

### Fixed

- `DataviewsAPI.get` and `query_data` no longer resolve and send a pipeline
  `sequence` when the caller gave none. The resolved value could be a staged
  draft step that never ran, so a read in draft mode failed with "Job failed".
  The API now picks the step, and one request fewer is made.
- `ExportsAPI.to_csv` (and `view.export.to_csv`) failed on every call under
  the async client: the download still used the `requests` streaming API. It
  now streams through `httpx`, with the same atomic write and error handling.
- `MammothClient.branch_out` returned an un-awaited coroutine instead of the
  dataset id.
- `DatasetsAPI.get_unstructured_rows` and `resolve_unstructured_rows` use the
  same `.../unstructured_rows` route (read and PATCH).
- Automations accept the task types, statuses and commands the routes accept
  today; `"restore"` is accepted as well as `"resume"`.
- Export specs default the properties the route defaults.
- An API error keeps the reason the API gave instead of a bare status code.

## [0.7.20]

### Fixed

- `AutomationPatchItem.value` (`mammoth/models/automations.py`) is typed
  `str | dict[str, Any] | PatchAutomationDetails`. Pydantic's default
  "smart" union mode picked the exact `dict[str, Any]` match over coercing
  a dict into `PatchAutomationDetails`, so any `op="replace",
  path="details"` patch built from parsed JSON — every real caller,
  including the CLI's `--input` and `mammoth_cli.embed.invoke` — left
  `value` a bare `dict` and failed `_validate_automation_patch_item`'s
  `isinstance(item.value, PatchAutomationDetails)` check with "must
  include at least one of: name, description, tasks, conditions" even
  when a field was set. Renaming an automation, or changing its
  description/tasks/conditions, was unreachable through any caller that
  builds the patch from JSON. The field now sets
  `union_mode="left_to_right"` with `PatchAutomationDetails` ordered
  before `dict[str, Any]`, so a dict is coerced into the structured model
  first. Reproduced live on koyal (mammoth-cli 2.0.46); see
  `tests/unit/test_automations.py::TestUpdate::test_update_details_patch_from_raw_dict_value`.

## [0.7.19]

### Fixed

- `AutomationsAPI.update` sent `path="status", value="resume"` to the backend
  verbatim. The backend's wire vocabulary for that path is `"suspend"` /
  `"restore"` (`apiv2/apiv2/automations/schema.py` `AutomationStatusValueEnum`
  in mvc-service), so a `"resume"` patch was rejected with
  `invalid_status_to_update` (400) and an automation could never be
  re-enabled once suspended. The SDK keeps `"resume"` as its own public
  value — consistent with `ScheduleStatus`'s `"pause"`/`"resume"` — and now
  translates it to `"restore"` on the wire.

## [0.7.18]

### Fixed

- `View.fill_missing` and `FillDirection` documented the directions the wrong
  way round. `FIRST_VALUE` is the forward fill (a blank takes the previous
  row's value in the `order_by` order); `LAST_VALUE` is the back-fill (the
  next row's value). Verified on release; behaviour is unchanged.

## [0.7.17]

### Added

- `View.rename_columns({"old": "new"})` and `View.sort_rows([["Col", "DESC"]])`:
  the web grid's column rename and sort, set as view display properties
  (`COLUMN_NAMES`, `SORT`). They add no pipeline task.

### Fixed

- A column renamed in the web app resolves by its new name: `View` applies
  the view's `COLUMN_NAMES` display property when it reads column metadata.

## [0.7.16]

### Added

- `MammothClient(api_token="mm_...", workspace_id=...)` authenticates with the
  API token (`Authorization: Bearer`), the server's primary credential. Tokens
  created in the web app today come without a separate secret.

### Deprecated

- `api_key` + `api_secret` (the `X-API-KEY`/`X-API-SECRET` headers) still
  work; pass either `api_token` or the pair, not both.

## [0.7.15]

### Added

- Math expressions accept a quoted display name: `Quantity * "Unit Price"`
  and `` Quantity * `Unit Price` `` parse the same as the bare form. An
  unknown quoted name raises `ValueError` naming it ("no column named
  'Unit Price'"); an unclosed quote says so.

## [0.7.14]

### Fixed

- `View._add_task` (every transform method) returned the server's submit
  record, whose `status` is `"processing"`, even though it had already
  waited for the pipeline to finish. Callers took that as unfinished work
  and polled the `future_id`. Outside draft mode the result now carries
  `status: "done"` and `pipeline_state` (the final state, `"ready"`); the
  other submit fields (`future_id`, `type_of_modification`, ...) are kept.
  In draft mode nothing has run, so the submit record is returned unchanged.

## [0.7.13]

### Added

- `View.to_dataset(...)` / `View.branch_out(...)` take `target_project_id`.
  A cross-project send is a persistent pipeline export step: the SDK reads
  the caller's user id once (`/self`) and sets the backend's `USER_ID`,
  `export_project`, `project_id` and `source_project_id` target properties;
  without them the backend answers 4GENR007 with no detail.
  `build_branch_out_params` accepts the same keywords and raises
  `MammothValidationError` when `target_project_id` is given without
  `user_id`.

## [0.7.12]

### Fixed

- `View._add_task` (every transform method) read the server's draft flag
  *after* submitting the task. The backend flips that flag to `dirty` when
  the new task carries a reference error (missing column, wrong column
  type), so the SDK skipped `wait_for_pipeline` and returned the job result
  `{"has_error": true, "status": "done"}` as success while the view sat in
  `ref_error`. Draft state is now read before the submit, and a result with
  `has_error: true` raises `MammothTransformError` (details carry the
  response; remove the task with `client.pipeline.delete_task`).

## [0.7.11]

### Added

- `ProjectsAPI.list` takes a server-side `offset`; `ProjectsAPI.list_all`
  walks the route's 100-row pages (`limit` above 100 is rejected by the
  backend with `4GENR007`). `ProjectsAPI.get(project="name")` now searches
  every page instead of the first 100 projects.

## [0.7.5]

### Fixed

- `TemplatesAPI.list` and `ConnectorAIAPI.session_list` read the bare JSON
  array those routes return and wrap it as `{"templates": [...]}` /
  `{"sessions": [...]}`; previously a successful HTTP 200 raised
  "Expected dict response from API".
- Dashboard artifact routes (`og_card`, `published_og_card`, `pdf_artifact`,
  `published_pdf_artifact`, `published_video_artifact`,
  `published_share_page`) no longer try to parse PNG/PDF/MP4/HTML as JSON.
  They return `{"content_type", "size_bytes", "sha256"}` plus `"text"` for
  HTML or `"content_base64"` for binary bodies (new `MammothClient._request_binary`).

## [0.7.4]

### Fixed

- `DatasetsAPI.rename` now sends the OpenAPI `DatasetPatchOperation`
  (`PATCH /datasets/{dataset_id}` with `{"op": "replace", "path": "name",
  "value": name}`). The previous `rename_dataset` operation on the plural route
  was rejected by the server with HTTP 400.
- `DatasetsAPI.update` and `DatasetsAPI.bulk_update` docstrings describe the
  plural route's actual contract (one `replace`/`name` operation mapping
  dataset ids to new names) instead of unsupported operation names.

## [0.7.3]

### Security

- Reject non-HTTPS API base URLs by default. Explicit HTTP is limited to
  loopback development endpoints and requires `allow_insecure_loopback_http=True`.
- Remove live-test credential defaults; the live suite now requires environment
  configuration and skips when it is absent.

## [0.7.2]

### Changed

- Preserve conservative response outcome metadata when a successful response
  has an unexpected shape, including mutation ambiguity.
- Mark effectful webhook GET dispatches as mutations and bound job waits using
  monotonic remaining-time accounting.

## [0.7.1]

### Changed
- Release the current SDK fixes and transformation updates, including safer
  pipeline/task outcome handling and clearer wrong-parent dataview errors.

## [0.5.1]

### Fixed
- **`mammoth.__version__` now reports the correct version.** It was pinned at
  `"0.4.0"` while `pyproject.toml` had moved to `0.5.0`, so the published 0.5.0
  wheel reported the wrong version at runtime. Both places are now `0.5.1` and
  kept in sync.

## [0.5.0]

### Added
- **DSL engine — pure builders.** COMBINE literal string-prefix support, a
  `limit` param on `build_window_params`, `DateComponent.YEAR_MONTH_NUMBER`
  (produces TEXT output in EXTRACT_DATE), and `FILTER_TYPE=SHOW` on SET value
  conditions. Export/dashboard builders now use `ExportTargetKey` /
  `DashboardSpecKey` constants instead of hardcoded wire keys.

## [0.4.0]

### Added
- **`mammoth._pure` — pure parameter builders.** A new side-effect-free layer
  (`mammoth/_pure/builders.py`, `mammoth/_pure/resolve.py`) that turns the typed
  transformation specs into backend task payloads with no HTTP/View dependency.
  Each `build_<op>_params` takes the typed specs (`ConversionSpec`, `CopySpec`,
  `SetValue`, …) plus a column map, so the payload-building logic is testable in
  isolation and reusable by agents. 100% line+branch test coverage.
- **`ViewHost` protocol** (`mammoth/_mixins/_host.py`) — a typing-only Protocol
  describing the `View` surface the ops mixins rely on, giving the mixins full
  static-type resolution (0 pyright errors, mypy `strict` clean) with no runtime
  effect.
- **CSV-upload integration test** (`tests/integration/test_csv_upload_e2e.py`)
  exercising the full lifecycle: upload → transform → verify transformed output
  → delete.

### Fixed
- **`convert_type(..., format=...)` now produces a valid payload.** `FORMAT` is
  emitted as `{"date_format": <fmt>}` (a dict) instead of a bare string, which
  the backend CONVERT validator requires.
- **`unnest()` and `json_extract()` no longer fail backend validation.** The
  UNNEST `LABEL`/`VALUE` output columns and each `json_extract` extraction item
  now carry an `INTERNAL_NAME` (previously omitted, causing a backend KeyError).
- **Filling empty cells with a literal no longer silently drops the value.**
  `build_fill_value_params` emits a VERSION-2 `SET` task with an `IS_EMPTY`
  condition on the target column (the FILL task ignores literal `WITH` values).

### Changed
- **Transformation mixins now delegate to `mammoth._pure`.** The eight
  `_mixins/*.py` modules build their payloads via the pure builders instead of
  inline dicts — one source of truth, no behavioral change to public method
  signatures.
- **Dependencies modernized and pinned (`==`).** `pydantic==2.12.5` (matches the
  Mammoth backend), and all runtime/dev dependencies upgraded to current releases
  with `pip-audit` reporting no known vulnerabilities. Python 3.14 is now
  supported for development; the published package continues to support 3.10+.
