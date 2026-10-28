# Changelog

All notable changes to `mammoth-io` are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (next mammoth-mcp-server)

- `undo` takes a change back. With what="trash" it restores views, datasets, dashboards and automations from the project's trash and reports which came back. With what="pipeline" it puts a view's pipeline back as one of its versions had it, and says when the view is still running again. The version list keeps the pipeline as it was just before, so a rollback can be taken back too.
- `list_trash` lists what a project's trash holds, 50 to a page with `next_offset`: each item's type and id (what `undo` takes), name, and days left before Mammoth deletes it for good.
- `get_pipeline` with `include_versions` lists the view's latest 10 pipeline versions, newest first, with what made each one.
- `edit_dashboard` has Mammoth's AI change a dashboard from a description (one turn of the editor's chat), gives it a new title, or both. It waits for the edit and reports `changed` and the AI's `message`. When `changed` is false, `next_step` says nothing was applied, whatever the message claims. The edit goes to the draft: on a published dashboard, `next_step` says the share link shows the old version until `publish_dashboard` runs again, and the tool never publishes. A board on the older engine can be renamed, and an AI edit of it is refused before anything is sent. An edit still going after the wait is reported as `editing` with its `job_id`; `edit_dashboard(job_id=...)` picks it up and reports what it did, sending nothing new. Mammoth's `changed` means the board was saved, not that it does what was asked: when the edit's job reports an ask that did not land (`asks`) or something it could not do (`could_not_do`), the tool reports `partial` and `not_done`. These fields come from mvc-service's dashboard edit job; a Mammoth without them reports neither.
- `get_dashboard` with `include_embed` gives the HTML that puts a dashboard on another site: an iframe with the board's embed key ("key"), a `TOKEN` the host's server signs per viewer ("signed"), or nothing more for a public board. It reports which sites may show the board, whether it is published, and what to tell the user: publish first, limit the sites, or (on "signed") that the workspace has no signing secret yet, so the embed shows nothing. It never returns the signing secret.
- `edit_dashboard` also sets the embed mode ("key" or "signed") and which sites may show the board (any site, or a list). Only what is named changes, and it applies at once: it is not part of the draft. Embedding has no tools of its own, to keep the tool list short.
- `upload_file` and `request_upload` take `append_to_dataset_id` and `mode` ("add" or "replace"): the file goes into that existing dataset instead of making a new one. `mode` sets the dataset's update method before the file is sent, puts the old one back if the upload fails, and stays on the dataset for every later upload. Without `mode` the dataset keeps its method, and the report says which one the upload ran under. Both tools reject `mode` without a target. Both run on the SDK's `client.appends`, the same code as the CLI's `file upload` into a dataset. A failed upload is reported as failed (`append_failed`, with the dataset's `status`), and a dataset that cannot be read says why (`read_error`) when the upload is still pending. If the browser upload fails and the old mode cannot be put back, the error says so (`update_method_kept`).
- An upload into a dataset reports `appended_to`, `update_method`, `rows_before`, `rows_after`, `rows_added` and, for "add", the `batch_ids` it added (`batch_id` when there is one). `check_upload` reports the same for `request_upload`. A new batch is the upload's only when its source names the file that was sent; others that appeared meanwhile come back as `unmatched_batch_ids` and are not offered for removal. A dataset that replaces offers no batch to remove: the old rows are gone.
- `get_dataset` with `include_batches` reads the dataset's update method (`mode`, `effect`, `schema_mapping`) and lists its batches, each file added with its `id`.
- `undo` with what="batch" removes `batch_ids` from a dataset that adds, and reports the rows before and after. It is destructive like the other `undo` kinds: it tells the model to ask the user first. It removes only batches an upload through these tools added to a dataset that was adding: the upload records each batch's mode when it lands (kept 90 days), so a mode changed later does not turn a replace into a removable batch. It refuses a batch with no such record, a dataset whose update method is replace, and a removal of every batch the dataset holds. These need no new tools.

### Changed (next mammoth-mcp-server)

- `delete_views` moves views to the trash, as the web app does, instead of deleting them for good. `undo` brings them back.

### Removed (next mammoth-mcp-server)

Five tools fold into others, so the tool list a client sends with every request is shorter:

- `get_transformation_schema`, `get_export_schema` and `get_automation_schema`: one `get_schema(kind, of)` answers all three, `kind` being "transformation", "export" or "automation". Only "automation" names a workspace and project.
- `list_dashboard_tags`: `list_dashboards` with `include_tags` lists the workspace's tags.
- `set_dashboard_tags`: `edit_dashboard` with `tags` replaces a dashboard's tags. Like the embed settings, they apply at once.

### Added (next mammoth-io)

- SDK: Repeat Rows. `view.repeat_rows(...)` adds a REPEAT step that repeats each row.
- SDK: `view.math()` takes `{name}` in an expression to use a workspace or project parameter.
- SDK: `json_extract` takes a key that is a path of keys and array indexes, not only a single key.
- SDK: From URL. `ConnectorDraftsAPI.link_preview` previews a link, `DatasetsAPI.follow_link` follows or copies a link dataset, and `DatasetsAPI.links` lists the linked datasets.
- SDK: bulk download. `ExportsAPI.bulk_download_plan`, `bulk_download_url` and `bulk_download`.
- SDK: project move. `SupportAPI.workspace_project_list`, `project_move_check`, `project_move_start`, `project_move_get` and `project_move_purge`. The server requires a tech admin.
- SDK: `AIAPI.generate_sql` takes an optional `current_query`, the SQL the rule holds now, which the intent changes instead of writing a new query.
- SDK: update method. `DatasetsAPI.get_update_method(dataset_id)` reads whether a new file replaces a dataset's rows or adds to them (the web app's "Update Method"). `DatasetsAPI.set_update_method(dataset_id, mode, schema_mapping=None)` sets it to `DataAdditionMode.REPLACE` or `DataAdditionMode.COMBINE`. Set reads the dataset's stored schema settings first and writes them back with only the mode (and `schema_mapping`) changed, so the other settings are kept.
- SDK: `FilesAPI.upload_result` returns `files`: the uploads that made no dataset, each with `action_needed`, either `sheet_selection_required` (with `sheets_info`) for a workbook or `password_required`. A file is matched to the upload by the `file_object_id` the upload job names, reading up to 500 of the project's newest files; without one (an older server), by name among the newest 50 files made after the job started. Uploading the same workbook twice reports each upload's own file. When the file list cannot be read, `files` is empty and `files_error` says why.
- SDK: appends. `client.appends.append(files, dataset_id, mode=None)` adds files to an existing dataset and reports what that did: `update_method` (the mode it ran under, `previous_mode` when it set one), `rows_before`, `rows_after`, `rows_added`, `batch_ids` (the batches whose source is the sent file) and `unmatched_batch_ids`. `mode` (`add` or `replace`) is set before the upload and put back if the upload fails. It waits until the dataset is ready and lists the new batch: the upload job ends before the dataset takes the rows in, while it still reads ready. `prepare` and `finish` are its two halves for a caller that sends the file elsewhere (a browser); `restore_mode`, `read_mode`, `rows` and `list_batches` are public too. The pure helpers (`mammoth.appends`: `describe_update_method`, `match_batches`, `describe_append`, ...) need no client. A dataset that ends in a failed status is reported with `append_failed` and `status`, not as an upload that added 0 rows; `read_error` says why a dataset could not be read while the upload is pending. `list_batches` stops at 10 pages or at a page with no new id. `refuse_batch_removal` is the one rule for when batches may be removed.
- SDK: `DatasetsAPI.get_update_method` also returns the dataset's remembered column choices, `ignored_source_columns` and `optional_destination_columns`, and `set_update_method` sends them back unchanged.
- SDK: `DashboardsAPI.share` takes `password` with `DashboardAuthType.PASSWORD` (8 to 128 characters); Mammoth stores only its hash and reports `options.has_password`. A Mammoth without password sharing (PRD-656) ignores the password, so check `options.has_password` after the share.
- SDK: `mammoth.api.automations.build_automation_create_body` and `build_automation_patch_ops` are public. They validate and build the request body that `AutomationsAPI.create` and `update` send; the CLI's dry run uses them.

### Changed (next mammoth-io)

- SDK: `DatasetsAPI.file_settings_update`: `delimiter`, `has_header`, `initial_skip_count` and `quotechar` are optional. A setting left out keeps the value the dataset stores, which the SDK reads first; if it cannot be read, the call raises `MammothValidationError`. Calls that pass all four are unchanged.


### Added (next mammoth-cli)

- CLI: `view transform repeat-rows` (Repeat Rows).
- CLI: `view transform math` takes `{name}` in an expression for a workspace or project parameter; `view transform json-extract` takes a key path (keys and array indexes).
- CLI: From URL: `dataset from-url preview`, `follow` and `links`.
- CLI: bulk download: `dataset download` and `dataset download-plan`.
- CLI: project move: `support workspace project list`, `move-check` and `move-start`, and `support project-move get` and `purge`. They are high-impact writes with `confirm_target`, like the other support writes. The five routes were internal-only before.
- CLI: `ai sql generate` takes `current_query` in its `--input` to refine a query. The CLI needs the next mammoth-io (the release raises the floor).
- CLI: `dataset update-method get DATASET_ID` and `dataset update-method set DATASET_ID --input '{"mode": "replace"}'` (`mode` is `replace` or `add`; `schema_mapping` is optional). The setting stays on the dataset, and so does every later upload into it. A set reports `previous_mode`, and `history undo` sets the previous mode back.
- CLI: `file upload` takes `mode` (`replace` or `add`) with `append_to_ds_id`, which sets the target's update method before the upload, and `sheets`, the sheet names to extract from a workbook that waits for a choice. If the upload then fails, the previous mode is set back. An append reports `update_method` (the mode it ran under, read from the dataset when no `mode` was given) and `batch_ids`, the new batches whose source is the uploaded file; a new batch that can't be tied to it is listed in `unmatched_batch_ids`. `--dry-run` with `mode` lists the mode change under `earlier_calls` beside the upload. `mode` with `wait_for_completion: false` is refused as a usage error (the mode is set only by the waiting append), and an append whose dataset ends in a failed status is an error (`job_failed`).
- CLI: an upload that waits on a person says so. A workbook with several sheets returns `needs_sheet_choice` with a runnable `file extract-sheets` command; a password-protected file returns `needs_password` with a `file set-password` command. Each file that made no dataset is listed in `files`, and `verify.needs_user` is set for these uploads.
- CLI: `batch list` marks batches whose source was deleted: `source_deleted: true` and `display_name`, the name without the " (Deleted)" suffix.
- CLI: `dataset file-settings update` takes any one of its fields; the fields left out keep their stored values.
- CLI: `--dry-run` of `automation create` and `automation update` runs the SDK's own validation and shows the request body the server would receive.
- CLI: `dataset interpretation confirm` returns the dataset's `columns` (name and type) and `row_count`.
- CLI: `how` recipes for replacing a dataset's data (`replace-data`), undoing an append (`undo-append`), choosing sheets (`pick-sheet`) and fixing a heading row (`fix-heading-row`).
- CLI: `dashboard share` shares a board with anyone who has its link and password: `--input '{"type_of_auth": "password", "password_file": "./pw.txt"}'`. The password is read from the file (8 to 128 characters) and never printed, shown in a dry run or kept in the history. Re-sharing as password without a file keeps the current password. It needs a Mammoth with password sharing (PRD-656). A Mammoth without it ignores the password: the CLI reads the share back, and when no password was stored it puts the earlier share back and fails with `unsupported_by_server` (exit 1, `details.share_restored` says whether the restore took). Until then `limitations` lists `dashboard-password-share`.


### Changed (next mammoth-cli)

- CLI: recipes carry a `version`, shown in `recipe list` and in the `recipe run` summary. `remove-duplicates` is version 2: it edits the named view in place, as version 1 did; pass `copy: true` to work on a copy and leave the original unchanged. The new optional `key_columns` makes only those columns decide a duplicate; without it whole rows are compared, as before. `summarize-by` is version 2: `group_by` takes one name (a string, as before) or a list of names, and the groups are ordered by `order_by` (default: largest result first). `blend-by-key`, `email-view`, `export-to-s3` and `dashboard-from-view` read the view's size first. New recipes: `filter-copy`, `create-projects`. `recipe run --dry-run` marks each previewed write as counted, an upper bound or not measured.
- CLI: `view transform discard-duplicates` takes `key_columns` (the columns that make a row a duplicate; every other column is ignored). `recipe run` refuses an input only when it still holds that input's own `<name>` placeholder.
- CLI: `history undo` of an append deletes the batch that upload added, and so its rows. It deletes nothing when the dataset's update method was replace (the old rows are gone) or could not be read, or when no new batch could be tied to the upload. It also refuses to delete a dataset's only batch (or all of them), and says why.
- CLI: a `need_action` hint points at `dataset interpretation preview` for a header or title-row problem; other cases still point at `dataset file-settings get`.
- CLI: `file delete` reads the file back after the delete and says it is gone (`deleted` names it); `automation delete` and `dashboard delete` do the same. A dashboard's read-back answers 403 once it is deleted, so that counts as gone only when the dashboard could be read just before the delete; otherwise the result is `delete_unverified`.
- CLI: the `file-dataset-refresh` limitation names both ways to load a new file into a dataset: add its rows (the default) or replace them.

### Deprecated (next mammoth-cli)

- CLI: `file upload`'s `staging_dataset_ids` (the temporary dataset an append makes, which the backend deletes) will be removed in the next release. Read `appended_to` and `batch_ids` instead.

### Removed (next mammoth-cli)

- CLI: the `mcp-task-edit` entry is removed from the limitations list.

### Fixed (next mammoth-cli)

- CLI: when `foreign_dataset_id` is missing, `view transform join` and `lookup` use the parent dataset from the cache.
- CLI: a deleted automation or dashboard reads as `resource_not_found`.
- CLI: backend error 5GENR012 is reported as `feature_disabled`.
- CLI: suggested commands no longer contain a `DASHBOARD_ID` placeholder.

- CLI: with `-o json`, `ndjson` or `yaml` the error envelope goes to stdout, like a success, instead of stderr, so a script reading stdout no longer gets an empty reply; the exit status is unchanged and stderr keeps only human hints and progress.
### Changed (next mammoth-io)

- SDK: `AIAPI.generate_sql` takes `dataset_id` and `dataview_id` as required keyword arguments (`dataview_id` was optional). Without a view the server writes against its default view 4, so the job failed with `NoSuchTable` for a table that is not the caller's. A call without either is refused before it is sent. The CLI needs the next mammoth-io (the release raises the floor).

### Fixed (next mammoth-cli)

- CLI: `view delete` waits for the delete job the server accepts (202) before it reads the view back, so a delete that takes a few seconds no longer reports `delete_not_applied` (#333).

## mammoth-cli 2.3.1 (2026-10-26)

### Fixed (mammoth-cli 2.3.1)

- CLI: `how` / `schema find` recipe matching: wrong matches, tied parts reported as unresolved, results no longer depend on the hash seed.

## mammoth-io 0.8.52, mammoth-cli 2.3.0 (2026-10-26)

### Added (mammoth-io 0.8.52)

- SDK: conditional reads. A GET whose response had an `ETag` is sent again with `If-None-Match`, and a `304 Not Modified` returns the kept body, so an unchanged resource is not downloaded twice. This covers every route the API tags (workspaces, users, projects, folders, browse, datasets, views, project resources) without a per-route list. The server changes a tag on every change event (a pipeline's status and row count included), and any write the client sends empties the kept bodies first. `MammothClient.etag_cache` is the store. By default it's `MemoryETagCache`, bounded by entry count and bytes; `MemoryETagCache.scoped(name)` gives one caller their own share of a cache that many callers use. Pass any `mammoth.etag.ETagCache` to keep the bodies elsewhere, or `None` to turn this off. With a `token_provider`, the kept bodies are keyed by the token sent too, so a client serving many users never offers one user's body to another.
- SDK: writes are safe to retry. Every write except a file upload carries a fresh `Idempotency-Key` (a caller's own key is kept). Once a response from the server echoes the key, the server is known to run a keyed write only once. From then on, a write whose connection dropped after it was sent, that got a 502/503/504, or that is still running from the first attempt (409 `4GENR038`) is sent again with the same key, at most twice, and runs once. A server that has never echoed a key gets no replays, as before. `mammoth.client.honours_idempotency_keys(base_url)` and `mark_idempotency_keys_honoured(base_url)` read and set what a process knows. If the write is still running after the retries (409 `4GENR038`), the error says `operation_state` `outcome_unknown`, not `failed`: it may still finish, so it must not be sent again.

### Added (mammoth-cli 2.3.0)

- CLI: typed output schemas (#315). Every command (346 reads and 505 writes) declares the shape of its `data` as `output_schema` in the manifest, and `schema get --full` returns it as a self-contained JSON Schema 2020-12. A command declares `openapi` (its `data` is the API's own `200` body), a named schema from `spec/manifests/output-schemas.yaml` (`{ref: NAME}`, shared between commands), or an inline schema. Writes share `WriteResult`: the `verify` block every API-backed write returns, the `state` read-back where the command has one, and the API's own fields. Transforms, exports, bulk deletes, agent turns and runs, and skill writes build on it (`TransformResult`, `ExportResult`, `DatabaseExportResult`, `BulkDeleteResult`, `AgentTurnResult`, `AgentRunResult`, `SkillWriteResult` and others); a delete with no response body is `null` (`WriteResultOrNull`). `output_schema` is always the real run's `data`. `--dry-run` of an API-backed write returns a report instead, and `schema get --full` returns its schema as `dry_run_output_schema` (`null` for a read). A contract test checks that each of the 851 commands declares one and that it resolves, and a fixture test runs each command's example (and each write's `--dry-run`) through the real handler and validates the result. It found two wrong read schemas, fixed here: `view data compare` returns `data`, not `rows`, and a folder's `created_by` can be text.
- CLI: ETag'd bodies are kept on disk between commands, so repeated `project list`, `dataset list` or `view get` calls download only what changed. There is one owner-only directory per credential, profile, server and workspace, under the user cache dir. A write through that credential empties it, and `auth login`/`auth logout` remove all of them. `MAMMOTH_CLI_ETAG_CACHE=0` keeps the bodies for one command only. Embedded calls (`embed.invoke(runtime=...)`) never touch the disk. The host's `EmbedRuntime` keeps one in-memory cache, capped at 4096 bodies and 128 MB, and each caller uses only their own scope of it, named by a digest of their credential. Two users therefore never share a body, even when the server gives them the same tag for differently filtered lists.
- CLI: every API request names the command that sent it in its `User-Agent`, which the server's request log already stores: `mammoth-cli/<version> (cmd=view.data.get; inv=3f9c2a1b7d4e; surface=run; agent=claude-code) mammoth-io/<version>`. `inv` is one id per command invocation, shared by all its requests and equal to the local run log's `run_id`. `surface` is `terminal`, `run` (a `mammoth run` line) or `embed`. `agent` is set from `MAMMOTH_AGENT`, or from the variable a coding agent sets (`CLAUDECODE`, `CURSOR_AGENT`, `GEMINI_CLI`, `CODEX_SANDBOX`), and never for an embedded call. Only identifiers are sent: no argument values, paths or data.
- CLI: steps in `mammoth run`. A line with `"name"` keeps its envelope, and a later line reads it in `args`, `input` or `flags` as `"{{steps.<name>.data...}}"`. `"when"` skips a line on a JSON condition (`eq`, `in`, `not`, `all`, `any`, `present`), and `"for_each"` runs a line once per item of a list, with `{{item}}` and `{{index}}`. A reference that does not resolve fails the line with `unresolved_reference` (exit 2); under `--dry-run` the line is planned instead. It is plain JSON: no code runs. A `$`-key other than a value operator (`$schema`, `$ref`) in a line is data. A `when` that is a bare string (no braces) is refused, as it would always be true. Under `--dry-run`, only a reference into the result of an earlier line plans the line; a malformed expression or a step no line makes fails it. A `for_each` over an empty list prints a skipped envelope with `data: []`, and with `--continue` it runs the items after a failed one.
- CLI: `mammoth history list`, `history show ID` and `history undo ID`. Every write is journaled on this machine (owner-only, under the log directory, rotated at 10 MB) with the `mammoth run` lines that reverse it: a trash is undone by a restore, an object a write made goes to the trash, and a pipeline edit returns the view to the pipeline version it had before. `history undo` takes one write's `inv` or a whole `mammoth run`'s `group`, runs the lines newest first through the normal command path, stops at the first failure (`outcome: partial`, exit 3) and needs a prompt or `--yes`; `--dry-run` previews them. A permanent delete, or a write with an effect outside Mammoth, is listed with the reason it cannot be undone. `MAMMOTH_CLI_JOURNAL=0` turns the journal off; embedded calls are never journaled. An append (`file upload` with `append_to_ds_id`) or an export into an existing dataset is never `created`, so its undo does not trash the dataset (rows cannot be taken out again, and the undo says so). Undo records only the `--profile` that was typed, not the default, so an env-token write is not undone as another account. An undo of a pipeline edit refuses when the view's pipeline changed since the edit (`--input '{"force": true}'` overrides), a stopped undo goes on from the line that failed, and two undos of one write cannot run together. The journal takes a file lock for each append, writes each record in one write, and keeps a run's plan in its own file (pruned after 60 days) so a rotation never drops it. Plans and named results are stored with credential-looking values replaced. `history list --input '{"limit": 0}'` is refused. An undo runs as the account the write used: a write made under a stored profile is undone under that profile even after `profile use` changed, and one made with `MAMMOTH_API_TOKEN` is refused with `undo_needs_token` when no token is set. The fingerprint that detects a changed pipeline redacts like the CLI output. When another process holds a write's undo, the writes already undone stay in the result (exit 3, `not_undone` lists the rest), and an undo's lock file is removed when it ends. A journal that cannot be written warns once on stderr.
- CLI: every write command declares how `history undo` reverses it in its manifest, as `undo`: `{strategy: inverse, command}` (run the named command with the write's own arguments, e.g. `agent run pause` and `resume`, `dataset file-settings update` and `undo`), `pipeline_version` (apply the view's version from before the edit), `trash_created` (trash what the write made), `manual` (a command reverses it but needs an id the write made, so it is named, not run) or `irreversible` with a specific reason (a permanent delete, an export to a named system, an email, a refund). `journal.compensation` reads the declaration instead of working it out from `mutation_class`. `scripts/build_manifests.py` derives the default; `spec/manifests/commands/<group>.yaml` overrides it, and a contract test fails a write with no `undo`. #311 An `inverse` undo line carries the `--confirm` target and the `--session` the original write named, so a high-impact reversal runs; an inverse that needs input the write lacks (`support partner client cancel-detach`) is `manual`. A `manual` entry says why it is not run, including for pairs that take the same arguments (`addon`, `project user`, `dashboard filter`). `file upload-folder` and `dataset create-from-pdf` are undone by trashing what they made; `view variants create` lists every view it made; a repeated `dashboard live-chart create` is not journaled as created.
- CLI: every success envelope carries `meta.run_id`, the invocation id: the same id as the run log's `run_id` (`log tail`), the journal's `inv` (`history show`) and the `inv` in the request's User-Agent. `embed.invoke(..., schema_version=1)` pins the envelope version a host was written against; `mammoth-cli/docs/envelope-compatibility.md` says what may change in a minor release and what needs a new `schema_version` (still 1: nothing in 2.3 breaks it).
- CLI: the servers that honour `Idempotency-Key` are remembered between commands (one owner-only file of API base URLs in the user cache dir), so a command's first write can be replayed safely too. Embedded calls never write it.
- CLI: `mammoth recipe list` and `mammoth recipe run ID --input '{"inputs": {...}}'` run a common task as one command. All 32 recipes in `discovery/recipes.json` are executable: append-rows, upload-dashboard, export-csv (takes `view_id` and `dataset_id`), share-dashboard, refresh-daily, blend-by-key, stuck-upload, export-powerbi, clean-data, cleanup-mine, upload-clean, join-files, lookup-column, add-calculated-column, extract-date-part, split-column, find-replace, fill-blanks-with-value, rename-columns, remove-duplicates, pivot-summary, top-n, filter-export-csv, export-xlsx, export-to-s3, email-view, dashboard-from-view, summarize-by, compare-views, refresh-now, undo-last-change and revert-view-version. The tasks that would replace a view's rows (pivot-summary, top-n, filter-export-csv) work on a copy. A recipe input can be a string, an integer, an array, an object or `any`. A recipe's steps run through the `mammoth run` path in one process, printing one envelope per step and a summary (`recipe`, `inputs`, `partial_lines`). A recipe that writes asks once (prompt or `--yes`), and `--dry-run` previews every step. `mammoth how` returns the recipe's `run_command`; `schema find` lists matching recipes (`recipes`), and `schema list` and `capability find` list `tasks`, before single commands. `scripts/eval_task_calls.py` counts the calls: 32 with recipes against 113 step by step for the 32 tasks (`mammoth-cli/docs/task-call-eval.md`). New error codes: `recipe_not_found`, `recipe_input_invalid`. `cleanup-mine` moves things to the trash (nothing is deleted for good), after a name check and a dependents dry run. A recipe never confirms a destructive line for the caller: it needs an explicit `--yes`, and the one prompt names those lines. An `any` input takes a list or a boolean. `upload-clean`, `upload-dashboard` and `join-files` skip the lines that need the upload's view when it has none, and end with a `dataset get` that shows the dataset's state. In `--dry-run` a `when` that reads a preview is still planned, and a step skipped by `when` is not taken for a preview. A binding with `$first` (or another operator) beside other keys is refused. Embedded in a host (`mammoth_cli.embed.invoke`), `recipe run` runs each step as a step of the host's call, with the host's login, project and session, and returns one envelope: the summary, with each step's envelope in `lines_run`. A recipe with a line the host cannot run (`file upload`, `history undo`) is refused before any line runs (`not_available_embedded`).
- CLI: `mammoth history resume GROUP` goes on with a `mammoth run` or `recipe run` that stopped (a failed line, Ctrl-C, a crash). It reruns from the first line that did not finish, and later lines still read the earlier lines' results (`{{steps...}}`). The run's lines and those results are kept in the journal; a result larger than 256 KB is not kept. If the run stopped while a write was being sent, resume refuses (`resume_outcome_unknown`): check the write, then pass `--input '{"from_line": N}'`. Needs a prompt or `--yes`; `--dry-run` previews. A failed named line is run again without an `already named` error. A write that was interrupted, timed out or lost its connection after it was sent makes resume refuse (`resume_outcome_unknown`) until `from_line` names the line to start from; a partial line of `recipe run` is not run again. A resume is recorded under the run it resumed, so a second resume and `history undo GROUP` see what the first did, and a `for_each` line goes on from its first unfinished item. A line that needs a secret the history does not keep is refused (`resume_secret_needed`). A `for_each` item result over 256 KB is journaled as omitted: a resume runs a read item again, refuses to repeat a write item (`resume_result_too_large`), and names the `from_line` that makes a result a later line reads. A resume also refuses a line that reads redacted data in an unfinished `for_each`.

### Changed (mammoth-cli 2.3.0)

- CLI: needs mammoth-io 0.8.52 or later: the response cache (`mammoth.etag`) and the safe write retries are not in 0.8.51.
- CLI: embedded in a host (`mammoth_cli.embed.invoke`), the discovery commands leave out what the host refuses: `schema list`, `schema find`, `capability find` and `capability list` drop the host-machine commands (`history`, `auth`, `config`, `log`, `skill`...) and those that read a local file (`file upload`); `recipe list`, the `tasks` and `recipes` of the index commands, and `how` drop the recipes that use them (append-rows, upload-clean, upload-dashboard, join-files, undo-last-change). When the best recipe for a goal is one of them, `how` says so (`matched: false`, a hint) instead of answering with a weaker recipe, and a several-part goal keeps the parts the host can run. A terminal run is unchanged.
- CLI: this is mammoth-cli 2.3.0, the ver3 architecture (#307): one command path with interceptors, a write journal with undo and resume, steps and recipes in `mammoth run`. Nothing breaks: no command, flag or input was removed or changed, and every envelope field was reviewed and kept, so `schema_version` stays 1 (the field review is in `mammoth-cli/docs/envelope-compatibility.md`). A host or agent written against 2.2 needs no change.

### Fixed (mammoth-cli 2.3.0)

- CLI: two embedded calls that start at the same moment in a fresh process no longer fail with `internal_error` ("partially initialized module 'mammoth.view'"). One call could read the SDK's view module while the other was still importing it.
- CLI: `dataset refresh` on a dataset made from an uploaded file returns `dataset_not_refreshable` with the ways forward (append the new file, or connect a cloud source), as `automation create` already did. Before, it was a generic `api_error` ("Invalid source type [4DSET048]").
- CLI: `numbers_stored_as_text` (and `dates_stored_as_text`) now catch a column whose missing values are written as a placeholder. Values like `N/A`, `NA`, `#N/A`, `-`, `--`, `null`, `none`, `nil`, `?` and `nan` no longer count against the column's share of numbers. Before, `100, 250, 75, N/A` (3 of 4, under the 80% bar) uploaded as TEXT with no warning. The finding still lists the placeholders, which the conversion makes empty.
- CLI: the `dashboard v3 generate` agent example now includes the required `intent`. Without it the backend refused the example with 4GENR007 ("intent must not be empty").
- CLI: `view version apply` waits for the pipeline to be rebuilt before it returns, so the view shows the applied steps. Before, it returned the job handle and a read straight after it still showed the old steps.
- CLI: `view conditional-format create` and `replace` list the allowed `color` swatches (red, amber, green, blue, purple, teal, coral, grey, `text-*`) in `schema get` and `schema find`, and refuse another word before the request with the list. Before, `color` was an open string and the list was only in the backend's 400.
- CLI: `schema get` takes ids separated by spaces (`schema get A B`) as well as by `,` or `;`. Before, it refused the second id with `unexpected_argument`.
- CLI: a `file upload` lists the datasets it made in `meta.opens` (`created: true`), as other creating writes already did.
- CLI: an append (`file upload --input '{"append_to_ds_id": N}'`) waits for the target dataset to take the rows before it reports. Before, it could read the target while it was still `processing`: `rows_added: 0` and a dataset health of `unknown`, though the rows did land. If the target is still `processing` when the wait ends, the result says `append_pending: true` with a warning.

## mammoth-io 0.8.51, mammoth-cli 2.2.100 (2026-10-23)

### Added (mammoth-io 0.8.51)

- SDK `mammoth.client.server_health(base_url, timeout=10)` GETs the public API v2 `/health` route and returns `status_code` and `latency_ms` (plus `version`/`commit` when the backend sends them). A non-2xx status is returned; a timeout or unreachable server raises `MammothAPIError` (#304).

### Added (mammoth-cli 2.2.100)

- CLI `mammoth doctor` has a `server` check: a GET of `<api>/health` (public, so it needs no login or project) that reports `status_code` and `latency_ms` (`healthy in 84 ms`), and `version`/`commit` when the backend returns them. It fails (and doctor exits non-zero) on a non-2xx answer, a timeout or an unreachable server, and still runs when auth fails, so an expired login and a down server read differently (#304).

### Changed (mammoth-io 0.8.51)

- SDK: waiting on a job polls every 0.5 s by default (`DEFAULT_JOB_POLL_SECONDS` was 2), so a short job returns sooner.

### Changed (mammoth-cli 2.2.100)

- CLI: `schema find` returns a compact result (the keys `full_schema_command`, `known_restrictions` and `matched_on` are left out; `schema get` has them). `schema find --full` returns the whole result, as before.
- CLI: `dashboard canvas get` leaves out null fields.

## mammoth-cli 2.2.99 (2026-10-22)

### Fixed (mammoth-cli 2.2.99)

- CLI: `schema find` now lists each inlined command's `positionals` in order with `required` (`view explore-panel set` is `VIEW_ID` then optional `DATASET_ID`). Before, only `accepted_fields` showed, with `dataset_id` as the one required id, so an agent passed the dataset id first. A field that an optional trailing positional can supply is no longer `required: true` in `accepted_fields` (`schema find` and `schema get`).
- CLI: the swapped-ids refusal ("N is a dataset id and M is its view; the order is VIEW_ID DATASET_ID", with the corrected command) now also covers every `VIEW_ID [DATASET_ID]` write that checks the parent (`view explore-panel set`, `edit`, `add-to-dashboard`, `export-image`, and `view optimize`), not only `view data get`.
- CLI: the `view explore-panel set` notes no longer say it "opens Explore cards in the UI"; it saves the calling user's panel and shows nothing by itself.
- CLI: `schema get view.transform.first-name` and `view.transform.update-column` no longer say a draft-mode step submits the draft; since 2.2.97 it stays staged (#298).

## mammoth-io 0.8.50, mammoth-cli 2.2.98 (2026-10-22)

### Added (mammoth-io 0.8.50, mammoth-cli 2.2.98)

- SDK `WorkspaceAPI.list(fields=...)` asks `GET /workspaces` for the given fields (default `"id,name"`, as before), e.g. `"id,name,download_file_types"`; `mammoth workspace list --input '{"fields": "..."}'` passes it (#272).
- CLI `workspace user list --project ID` lists that project's members with their roles; `schema find` reaches it for "project members" and "my role". The project was dropped before (#256).
- CLI `--reveal` on `dashboard embed secret rotate` and `dashboard embed preview-token create` prints the new signing secret or preview token, which the API shows only once. Without it they stay masked as before (#278).

### Changed (mammoth-cli 2.2.98)

- CLI: a plan or AI-quota refusal (`4SUBS101`–`4SUBS106`, e.g. `AI_QUOTA_EXHAUSTED`, `FEATURE_NOT_AVAILABLE_ON_PLAN`) is the new error code `plan_limit` (exit 4), with the backend's message and a hint about the plan and quota, instead of `authorization_required` with "check the ids" (#254).
- CLI: `dashboard live-chart create` waits for the chart's bake job (bounded by `--job-timeout`) and reads the chart back; the result keeps `dashboard_id` and `job_id`. Before, it returned the queued job with no wait or readback (#281).
- CLI: `dashboard live-chart create`, `dashboard template apply` and `dashboard v3 generate` send an explicit `--project` as the new board's `project_id`; without it the server still uses the source view's project (#280).
- CLI: `view export rest-fill` refuses `wait` and `timeout` in `--input` instead of ignoring them; it always waits, for at most `--job-timeout` seconds (#279).

### Fixed (mammoth-io 0.8.50, mammoth-cli 2.2.98)

- SDK `DashboardsAPI.embed_lifetime_set` refuses a `token_ttl` that is not an integer (a bool, a string) as well as one outside 60–3600. CLI `dashboard embed lifetime set --dry-run` applies the same check, and its example now uses `900` instead of the invalid `1` (#283).

### Fixed (mammoth-cli 2.2.98)

- CLI: a backend `PERMISSION_ERROR` (`4PERM002`) sent as an HTTP 400 is `authorization_required` (exit 4) with the backend's message, not a generic `api_error` telling the caller to correct the request (#277).
- CLI: `dashboard embed config get` shows `has_signing_secret` as `true`/`false`; key redaction never masks a boolean (#278).
- CLI: `--help` and `schema get` list the values of a `Literal` field: `view export download` shows `file_type (csv | xlsx | json | ndjson | xml | yaml | parquet)` and `schema get` reports its `enum`. A long type in `--help` is cut at a word with `...`, never inside a value (it showed `'par`). The command's docstring and example name `file_type` (#282).
- CLI: `schema get view.summary` reports `dataset_id` as optional, as its positional is, and `schema find` sends column-statistics searches to `view data profile` rather than `view summary` (#284).
- CLI: `file upload` of a file that made no dataset (a PDF waiting for table extraction) reports `status: no_dataset` with a message and `verify.needs_user`, not `ready` (#255).

## mammoth-cli 2.2.97 (2026-10-22)

### Fixed (mammoth-cli 2.2.97)

- CLI: `view transform first-name` and `view transform update-column` no longer submit the draft of a view in draft mode. The step stays staged (`status: staged`, no run to wait for) like every other transform, and draft mode stays on until `view draft submit`. Before, the first such step on a draft with no other staged steps ran at once, ended draft mode and reported `draft_applied`. Outside draft mode nothing changes.

## mammoth-io 0.8.49, mammoth-cli 2.2.96, mammoth-mcp-server 0.2.8 (2026-10-22)

### Added (mammoth-io 0.8.49, mammoth-cli 2.2.96)

- SDK `MammothClient(default_headers=...)` and `MammothClient.add_default_headers()`: extra headers (a forwarded `Cookie`, a run id) that go on every request this client makes, over the credential headers. They are kept on the client and added per request, never written to a shared `http_client`, so two clients on one pool cannot send each other's. `set_workspace_id` and the credential headers already worked this way; no SDK code writes per-user state to `session.headers` or `session.cookies` of a shared client any more (the owned client still mirrors its headers to its own session). `download_session` stays per client: it carries no credentials and opens connections only for signed export URLs.
- CLI `mammoth_cli.embed.EmbedRuntime`, `shared_pool()` and `invoke(..., runtime=...)` (also `invoke_many`): an opt-in host-owned event-loop thread and one cookie-less `httpx.AsyncClient`. Embedded calls given a runtime send their requests through its pool and run their coroutines on its loop, so keep-alive connections are reused across calls and users (no new TCP + TLS handshake per call) and a call made from inside a running loop starts no helper thread. Each call's credentials, forwarded headers and agent-run header stay on its own requests. A runtime is used only with an SDK that has `default_headers` (mammoth-io 0.8.49); with an older one, or a closed runtime, each call keeps its own client as before. Closing a runtime cancels calls in flight (their callers get `RuntimeError`, not a hang), and `run()` from the runtime's own loop thread raises instead of deadlocking. Work on the shared loop must not block: a synchronous `token_provider` or a synchronous workspace lookup would stall every user; with an `api_token` login the workspace is known before the call (and a `workspace_id` hint skips even that), so neither happens. Without `runtime=` nothing changes. On a dev server 340 ms from the caller, `project list` took a median 2.6 s with a client per call and 1.7 s on a shared runtime (interleaved, 15 warm calls each).

### Added (mammoth-cli 2.2.96)

- CLI `mammoth_cli.embed.invoke_many(commands, *, login, ..., stop_on_error=True)`: an embedding host runs several commands as one user and gets one envelope per command, in order. The commands share one scope, so each one reuses the client and connection the earlier ones opened for the same login and project (the way the lines of a `mammoth run` do); the services close when the batch ends. It stops at the first command that fails (an `error` envelope or a non-zero `meta.exit`) and gives each later command a `skipped` error envelope with its `index`, `reason: earlier_command_failed` and the `failed_index`; `stop_on_error=False` runs them all. Nothing is written to stdout. Each envelope of `invoke` and `invoke_many` carries the command's wall time as `meta.elapsed_ms` (`error.elapsed_ms` on a failure; 0 for a `skipped` one). The project-pin read (`GET /workspaces/current`, which an embedded call cannot cache on disk) is made once per batch, not once per command, also inside a `mammoth run`. Five `project list` calls against koyal took 5.2s as one batch with a workspace hint, against 9.9s as five `invoke` calls (one run each).
- CLI: every envelope carries its exit status: `meta.exit` on a success (0, or 1 or 3 when a write's read-back failed or was partial) and `error.exit` on a failure, the same number a `mammoth run` line shows. An embedding host no longer maps `error.code` to a status itself.
- CLI: `schema get` marks a positional or input field that takes a path on the machine running the CLI with `kind: local_path` (manifest `positionals[].kind`, `accepted_fields[].kind`), so a host does not match the help text.
- Every command now has a `server_status`: `served` (the production server serves its routes), `pending` (a route is on server master but not in production yet) or `removed_on_server`. It is derived at build time from the pinned prod spec (`spec/openapi/openapi.json`) and the pinned master spec, through the same command -> SDK method -> route mapping as the release capability matrix (`scripts/build_server_status.py`, run by `scripts/build_manifests.py`; stored in `spec/manifests/server-status.json` and the compiled manifests), and shown in `schema get` (brief and `--full`), the `schema list FAMILY` and `schema find` rows, and `capability` entries. The prod pin was re-pinned on 2026-10-22 and now serves every operation on the master pin, so no command is pending at this release; a command becomes pending whenever the master pin is ahead of the prod pin. Running one from a terminal is unchanged.
- `mammoth_cli.embed.invoke(..., hide_pending=True)` refuses a `pending` command with the usage-class error `pending_server_release` before any request, and leaves such commands out of `schema list`, `schema find` and `capability` for that call.

### Changed (mammoth-cli 2.2.96)

- CLI: an embedded token login (`ExplicitLogin(api_token=..., workspace_id=...)`) now takes the workspace id as a hint instead of refusing it, so a call no longer asks the server `GET /workspaces/current` first. A wrong hint is caught on the first refusal (koyal answers a request to another workspace with a 401 "Invalid token"; a 403 is checked the same way): the CLI then asks the token's own workspace once and, when it differs, returns `workspace_mismatch` (exit 3, with both ids in `details`) instead of the refusal. A login without the hint is unchanged.
- CLI embedding (`mammoth_cli.embed.invoke`): the commands that take a local path are refused as `not_available_embedded`, derived from the `kind: local_path` marker. New in the list: `dashboard chat attachment upload`, `connector draft sample`, `collection files upload`, `dashboard attachment-create` and `dashboard import-workbook` (the last keeps its `intent_only_dashboards` refusal); a command added later with a marked path is refused without another edit.
- CLI embedding: text a command writes to stdout during an `invoke` call no longer reaches the host process; the call returns a `stray_output` error (the first 500 characters in `error.details.stdout`) so the command gets fixed. Text on stderr (an SDK log line, a Python warning) is kept out of the host's stderr too but does not fail the call: it comes back as `meta.stderr` on a success or `error.details.stderr` on a failure, up to 500 characters. A per-context stream guard does this, not `contextlib.redirect_stdout`, so concurrent calls and the host's other threads do not see each other's output; it refuses bytes like a real text stream and routes `.buffer` the same way.
- CLI embedding: a call that produced more than one envelope returns a `multiple_envelopes` error (listing what it saw) instead of silently keeping the last.
- CLI embedding: `MAMMOTH_AGENT_RUN` in the process environment is ignored; the run header comes from `ExplicitLogin.headers`.

### Changed (mammoth-io 0.8.49)

- The generated dashboard models (`mammoth.models.dashboard_generated`) and wrappers are regenerated from the 2026-10-22 production spec: chart-type models are added, and `SwapFitParams` gains `page_id` and `target_dataset_ids` (`target_dataview_ids` is now optional).
- The SDK and the CLI require `certifi>=2026.10.19`, which drops the distrusted eMudhra CA (PRD-3142).

### Fixed (mammoth-cli 2.2.96)

- CLI: the lazily built command tree (`LazyLeafCommand`, the cached Click root) is built under a lock, so threads making their first call together build it once.

### Fixed (mammoth-mcp-server 0.2.8)

- MCP server: the `mammoth-io` floor is raised from `>=0.8.39` to `>=0.8.47`. The server builds every client with `MammothClient(http_client=...)`, which is new in mammoth-io 0.8.47, so 0.2.7 installed next to an older SDK failed on its first request with `TypeError: unexpected keyword argument 'http_client'`.
- MCP server image: `deploy/Dockerfile` refreshes the system CA certificates on every build, so the distrusted eMudhra CA is dropped (PRD-3142).

## mammoth-io 0.8.48, mammoth-cli 2.2.95 (2026-10-22)

### Added (mammoth-io 0.8.48, mammoth-cli 2.2.95)

- CLI `mammoth run [FILE|-]` runs many commands in one process from JSON Lines (`{"cmd","args","input","flags"}` per line; optional `id`). One credential load, one SDK client and connection pool, warm in-process caches; one JSON envelope per line on stdout (with `line`, `cmd`, `exit`) and a final summary envelope. It stops at the first failing line (exit = that line's code); `--continue` runs every line and exits non-zero if any failed. Each line confirms exactly as the single command does (`run` takes no global `--yes`), `--dry-run` applies to every line, and `run`, `auth login` and `auth logout` inside a run are refused. Ten read commands take about 12.5s as one `mammoth run` against about 27s as ten processes on the same jupiter link (median of 5 each).
- SDK `MammothClient.dataview_dataset_store` and `PipelineAPI.forget_dataview_dataset()`: an optional store (`mammoth.api.pipeline.DataviewDatasetStore`) that keeps which dataset holds a dataview between processes. The SDK reads it before `GET resources/dataview/{id}` and writes each answer it learns; a store that fails counts as empty.
- CLI: the view -> dataset answer is kept on disk (`view-datasets-<fingerprint>.json` in the cache dir, one file per credential, mode 0600, atomic writes, at most 5000 entries). A 404 on a request made with a remembered dataset drops the entry and retries once; `auth login` and `auth logout` clear it; `MAMMOTH_CLI_VIEW_DATASET_CACHE=0` turns it off. `view task list 290` drops from 2 requests to 1 (the lookup is skipped), about 0.5s of a ~2.5s command at the time of measuring.
- SDK `client.support` gains 45 admin-console methods, and the CLI gains the matching `support` commands. They were the last production operations left unmapped. Billing actions (`support billing start-trial`, `end-trial`, `retry-payment`, `refund`, `change-plan`, `cancel-subscription`), deals (`support deal list`, `get`, `create`, `update`, `activity`, `preview-entitlement`, `opt-in`, `move-to-partner`, `cancel-move-to-partner`), partners (`support partner list`, `get`, `create`, `update`, `activity`, `billing`, `invoices`, `charge-invoices`, `send-payment-link`, and `support partner client list`, `delete`, `detach`, `cancel-detach`), identities (`support identity list`, `get`), catalogs (`support plan catalog`, `support entitlement registry`, `support connector bucket-impact`), the admin home (`support search`, `triage`, `usage-tiles`) and workspace administration (`support workspace activity`, `entitlement`, `deal-seed`, `chargebee-cancelled`, `archive-info`, `archive`, `restore-archive`, `support workspace invite cancel` and `resend`). Writes need a super or tech admin and, like every `support` write, `--yes --confirm TARGET`; `--dry-run` shows the call without sending it. `support partner client delete`, `detach` and `cancel-detach` confirm the WORKSPACE id (the second argument), not the partner id. `support billing refund` needs exactly one of `amount` (positive whole cents) or `full: true` (a JSON boolean) (SDK: `billing_refund(ws, amount=...)` or `full=True`), so a refund is never full by omission; its confirmation names the amount or FULL, and refund and `partner client delete` are classed destructive, so `--dry-run` reports `irreversible: true`. `support billing start-trial` says it replaces the workspace's billing and cancels a live paid Stripe subscription; `support deal move-to-partner --when now` says it cancels the subscription prorated and refunds the unused time; a `support deal update` to `status: cancelled` and a `support deal create` with no workspace id or `workspace_create.name` are called out or refused. `support workspace archive` also needs the workspace name typed in `confirm_name`; `archive` and `restore-archive` answer 202 and queue a job (`returns_job`): poll `support workspace archive-info`. `support identity list` follows its pages to the end (invitees with no account included; `limit` is a page size from 1 to 100; the result is the merged list without per-page `offset`, `limit` or `next`). Partner `status` is `active` or `inactive`. SDK methods check `days`, `when`, `price`, `amount`, ids (real integers only), `billing_interval` (`monthly`, `yearly`, `annual`) and `storage_class` locally before any request, and raise `MammothValidationError`.
- Agent access. SDK `AgentsAPI.access_me`, `access_settings_get`, `access_settings_update`, `access_grants_list`, `access_grant_give`, `access_grant_update`, `access_grant_revoke`, `access_people`, `access_tree`, `access_project_askers`, `access_reach`, `access_requests_list`, `access_requests_mine`, `access_request_create`, `access_request_resolve`, `access_request_add_to_context` and `access_chart_save`, with CLI `agent access me|settings get|settings update|grant list|grant give|grant update|grant revoke|people|tree|askers|reach|request list|request mine|request create|request resolve|request add-to-context|chart save`. `grant give` needs `--yes` (it tells the people); `grant revoke` prompts or takes `--yes` (a `--confirm` must equal the grant id); `request resolve` is irreversible (a closed request cannot be reopened and the requester is told), so it prompts or takes `--yes` and its `--dry-run` says `irreversible`; `settings update` changes the AI Agent for the whole workspace, so it needs `--yes --confirm WORKSPACE_ID` and its `--dry-run` reads the current settings and shows each field from its current to its new value. The `--dry-run` of `grant update`, `grant revoke` and `request resolve` names the grant or request. Every dry run checks its input the way the real call does (empty `emails` or `items`, a bad `level`, a `status` of `open`, `items: []` on `grant update`) and stops with the same usage error. SDK `AgentsAPI.access_grant_update` refuses `items=[]` (the server wants at least one).
- Agent turn feedback. SDK `AgentsAPI.turn_feedback_list` and `turn_rate`, with CLI `agent session feedback list SESSION_ID` and `agent turn rate SESSION_ID TURN_ID` (`rating` is `up` or `down`).
- Held plan change. SDK `BillingAPI.stripe_held_change_get` and `stripe_held_change_cancel`, with CLI `billing stripe held-change get` and `billing stripe held-change cancel` (`--yes --confirm WORKSPACE_ID`). The cancel is irreversible: it voids the unpaid invoice, and if the invoice was already paid the change is applied instead (`landed: true`). It reads the held change first, and its confirmation and `--dry-run` (`irreversible: true`) name the plan and billing cycle.
- Plan entitlements. SDK `SupportAPI.plan_update_entitlements` and CLI `support plan update-entitlements PLAN_ID` (`--yes --confirm PLAN_ID`). It changes what every workspace on the plan is granted; its confirmation says so and its `--dry-run` names the plan and the new values (the plan read has no current values, so the old ones show as `not readable`; legacy and system plans are read-only).
- Connections. SDK `ConnectorsAPI.list_all_connections` and `test_connection`, with CLI `connector connection list-all` (every connection in the project, across connectors) and `connector connection test CONNECTION_KEY` (a health check that is kept).
- Task preview cancel. SDK `PipelineAPI.preview_cancel` and CLI `view task preview-cancel VIEW_ID JOB_ID`.
- Open tables links. SDK `DatasetsAPI.tool_claim_get` and `tool_claim_redeem`, with CLI `dataset tool-claim get` and `dataset tool-claim redeem` (token in `--input`).
- Dashboard chat. SDK `DashboardsAPI.chat_attachment_upload` and `unpublished`, with CLI `dashboard chat attachment upload DASHBOARD_ID FILE` (the result's `ref` goes in a chat turn's `attachments`) and `dashboard unpublished DASHBOARD_ID`. The upload refuses an empty file, a PDF or Word file over 20 MB, or any file over 50 MB before sending; a picture is also refused by the server when it is still over 2 MB after being scaled to 1500 px.
- The OpenAPI inventory marks three more operations internal-only: `GetChatAttachment` (editor chat thumbnails), `StreamJob` (a server-sent push of job progress; it works over curl but only arrives sooner than polling for task previews, and `job wait` follows the same job) and `StartToolClaim` (the public sign-up step of an emailed link).
- Dashboard figure data (server master, not in production yet). SDK `DashboardsAPI.figure_rows`, `figure_drill`, `published_rows` and `published_drill`, with CLI `dashboard figure rows|drill DASHBOARD_ID` and `dashboard published rows|drill URL`. They name the figure by its `PAGE:SLOT:ID` key (a key of `meta.figures` in `dashboard canvas get`), wait for the job, and return the handle's `descriptor_ids` with the `results` they point to. A published board answers `rows_disabled` or `drill_disabled` until the figure lets readers see rows or drill.
- Describe a chart. SDK `DashboardsAPI.figure_recipe` and CLI `dashboard figure recipe DASHBOARD_ID`: a description in, a figure spec out (`added`); nothing is saved until you pass it to `dashboard figure add`.
- Workspace chart types. SDK `DashboardsAPI.chart_type_list`, `chart_type_create` and `chart_type_delete`, with CLI `dashboard chart-type list|create|delete`.
- Watched folders and file routing. SDK `AutomationsAPI.watched_folders`, `runs`, `preview_routes`, `set_route_order` and `add_run_file_anyway`, with CLI `automation folders`, `automation runs AUTOMATION_ID`, `automation route preview|order FOLDER_RESOURCE_ID` and `automation run-file add-anyway RUN_FILE_ID` (asks first: it adds a file the routing held back).
- Connector drafts. New SDK sub-client `client.connector_drafts` (`list`, `create`, `known_sources`, `get`, `update`, `discard`, `sources`, `preview_source`, `join_candidates`, `fill`, `sample`, `browse`, `open`, `read_tables`, `save`), with CLI `connector draft ...` and `connector draft source list|preview|join-candidates`. `sample DRAFT_ID PATH` uploads a local file, refused before sending when it is missing or over the server's limit; `save` waits for its job. `--dry-run` of `connector draft discard` and `dashboard chart-type delete` names the draft or chart type it would remove.

### Changed (mammoth-io 0.8.48, mammoth-cli 2.2.95)

- CLI: `view list DATASET_ID` reads the views and the dataset's name together instead of one after the other (identical output, compared on jupiter). `view get` already read the view and the dashboards together.
- CLI: `view list` summaries read each view's stored column stats with `POST .../profile_generation` (`action: stats`). This is the only route that serves them; it is a read (permission `dataview.get`, no job, nothing written), so it stays.
- CLI: faster start-up for commands that run and for leaf `--help`. A run no longer builds the `--help` text (it imported the schema and contract layers), `--help` reads the summary from the generated index instead of importing the handler module, and the OAuth module (with `http.server`/`webbrowser`, now in `context/oauth_loopback.py`), PyYAML and the SDK pipeline module load only on the path that uses them. CPU time on a quiet machine, min over 11 to 21 runs, same machine, before to after: `project list --profile ...` 711 to 555 ms, `view list --help` 772 to 519 ms, `project list --help` 775 to 669 ms; `--version` and root `--help` are unchanged (26 and about 280 ms). A unit test pins which modules a run and a leaf `--help` must not import.
- SDK: a transform (every `View` method that adds a step) reads the pipeline once after the submit, for both the draft state and the first poll of the wait, instead of reading the draft state before the submit and polling after it. A step that settles at once costs the submit, one pipeline read and the metadata refresh. A pipeline in `ref_error` with auto-run on is still a failed step, never a staged draft.
- CLI: a view transform builds its View from the view metadata its checks already read, instead of fetching it again. With the SDK change, `view transform math` on koyal went from 18 to 16 requests (one view read and one pipeline read fewer, about 1.5s); a step in draft mode is still reported `staged`.

### Deprecated (mammoth-io 0.8.48, mammoth-cli 2.2.95)

- `BatchesAPI.create`: `change_map` is no longer sent (the batches route has no such field and dropped it) and passing it raises a `DeprecationWarning`. CLI `batch create` adds a `warnings` entry when the input carries it.

### Removed (mammoth-io 0.8.48, mammoth-cli 2.2.95)

- 43 CLI commands and the SDK calls behind them, whose server routes exist on neither server master nor production. Each one failed against the server, or the CLI refused it before sending:
  - `data-app` (12 commands) and `client.data_apps`: Data Apps were retired on the server on 2026-10-05; collections replace them.
  - `agent` definitions (29 commands: `agent list/get/create/update/delete/publish/disable/roles`, `agent charter`, `goldens`, `memory`, `scratch`, `projects`, `team`, `feedback list`, `access set`) and `client.agent_definitions`: the server feature was never merged. Agent chat, sessions, runs, plans and `agent access` grants are unchanged.
  - `addon list` and `AddonsAPI.list` (the server has no add-on list; the add/remove commands stay), and `user change-password` and `UserProfileAPI.change_password` (the web app's Profile settings > Reset Password does this).
- `ExportStatus.QUEUED`: the server's export statuses have no `queued`.

### Fixed (mammoth-io 0.8.48, mammoth-cli 2.2.95)

- A `--dry-run` that cannot find its target in a list now names that list's command in its hint (`mammoth dashboard chart-type list`, `mammoth agent action list`), not a guess from the target's kind (`mammoth chart list`).
- SDK models now match the server's request and response shapes, checked against the OpenAPI spec:
  - `ProjectPatch` takes `patches` of `{op, path, value}` (path `name`, `properties` or `agent_memory`); `AddUsersToProject` takes `users` of `{user_id, role}`; `ProjectUserPatch` takes `patch` of `{op: replace, path: permissions, value: <role>}`; `ProjectsPatch` takes `patches` of role operations across projects. Roles are `project_admin` or `project_analyst`. The old shapes (`user_emails`, `role="editor"`, `project_ids`/`operations`) were never accepted by the server; no SDK call used them.
  - `DatasetPatchRequest` accepts `patches` (a list) as well as `patch` (one operation), and refuses neither; `DatasetSchema.created_by` may be a string.
  - `DataviewSchema.dataset_id` reads the server's `ds_id`; `ActiveUsersList` reads `active_users`, with each user's `id` as `user_id`.
  - `DashboardBiPreflightResponse`: only `exportable` is required; the counts default to 0 and `refusals` to empty.
  - `clientapps.PatchOperation.value` may be a list of strings.
- `format_date_range` sends `%Y-%m-%dT%H:%M:%S.%fZ` in UTC, the only format the server parses; an aware datetime is converted to UTC.
- CLI `mammoth run` refuses `run`, `auth login` and `auth logout` by the command the line resolves to in the Click tree, not by the literal `cmd` string: `{"cmd":"auth","args":["logout"]}` and `{"cmd":"run inner"}` are refused like `{"cmd":"auth logout"}`.
- CLI `mammoth run`: Ctrl-C ends the whole run, `--continue` or not (rest `skipped`, exit 130); lines split on `\n` only (a raw U+2028 in a JSON string no longer breaks the line) and a UTF-8 BOM is accepted; FILE defaults to stdin and `--continue` works in any position (`mammoth run --continue < lines.jsonl`); `sys.exit()`/`sys.exit(0)` and a zero exit with no envelope count as success; a negative number (`-5`) is an argument, not a flag.
- CLI: a remembered view -> dataset answer is retried after a 404 only for read-only calls (a write may have done part of its work), and an SDK without the store (mammoth-io 0.8.46) simply runs without the cache.

### Changed (mammoth-io 0.8.48, mammoth-cli 2.2.95: server master re-pinned)

- The master OpenAPI snapshot is re-pinned from `master-20261002` to `master-20261021` (`origin/master@29fe5d1ab8`, 756 operations), exported offline from server source as before. The release capability matrix now covers 769 operations, up from 545. 145 of the 146 `PENDING_SERVER_RELEASE` routes are on master and are removed from the list; only the agent-run verb helper's variable-suffix route stays.
- 33 SDK routes are on neither master nor production, so the matrix reports them `removed_on_server`: `data-app` (12 commands; Data Apps were retired on the server on 2026-10-05, replaced by collections), `agent` definitions, charter, goldens and memory (19), `addon list` and `user change-password`.

### Release note (mammoth-io 0.8.48, mammoth-cli 2.2.95)

- The cache uses `PipelineAPI.stored_dataview_resolutions()` and `DataviewDatasetStore`, which are new in mammoth-io 0.8.48. The CLI's `mammoth-io` floor in `mammoth-cli/pyproject.toml` is therefore `>=0.8.48`; on an older SDK (0.8.46 and earlier) the code runs without the cache.
- The 28 routes the agent access, held-change, entitlement, connection, task-preview-cancel, tool-claim and unpublished commands call are served by the pinned server master (`origin/master@29fe5d1ab8`), so they are not in `PENDING_SERVER_RELEASE`: the list holds one entry, the agent-run verb helper's variable-suffix route (see the re-pin note above). The server release that puts master on production is not out yet, so on production these commands can still answer 404.
- SDK: `connection_key`, `session_id` and `turn_id` are URL-encoded in their request paths.
## mammoth-io 0.8.47, mammoth-cli 2.2.94, mammoth-mcp-server 0.2.7 (2026-10-21)

Covers mammoth-io 0.8.46 to 0.8.47, mammoth-cli 2.2.93 to 2.2.94 and mammoth-mcp-server 0.2.5 to
0.2.7; each section names the version it shipped in.

### Added (mammoth-mcp-server 0.2.7)

- A connection the user limited to several projects on the consent screen may act in each of them. The token's projects are read from Mammoth's `projects` (and from `project` alone, on a Mammoth older than multi-project sign-in). `list_projects` lists every pinned project, a project outside them is refused naming them all, and `request_upload` takes no project only when the connection has exactly one.

### Added (mammoth-mcp-server 0.2.6)

- `edit_transformation_step` changes one step of a view's pipeline: `replace` (the step does a new operation, built on the columns that step reads, and a column it makes keeps its internal name so later steps still find it), `suspend` or `restore`. In draft mode the change is staged, and only the steps it breaks are blamed on it. Otherwise it runs at once, and a change that makes a step fail that did not fail before is undone, with the failing steps and their errors in `problems`. A change Mammoth refuses because a later step reads a column it removes names those columns and says to make the changes together in draft mode. A step of another view is refused before anything is sent.
- `get_pipeline` lists the steps in error under `problems` and says what to do in `next_step`; it also says when changes are staged in draft mode and have not run, steps in error or not. `manage_draft` "run" reports the steps the run broke.
- `get_help` topic `pipeline`: when to run at once and when to use draft mode, and what to do when a step fails.
- `edit_export` changes one export of a view: `replace` (only the settings named change, null drops one, a masked password is kept, a scheduled export keeps its schedule; nothing is sent), `suspend`, `restore`, or `run` (sends the rows now and reports the run's rows or its error, with how to fix it; a run Mammoth has not recorded yet is `run_pending`, never an older run). An export of another view, and a command that cannot do anything (suspend twice, run a suspended export), are refused before anything is sent.
- `get_export` shows the export's recent runs, with each failed run's error.

### Fixed (mammoth-mcp-server 0.2.6)

- An operation whose expression names a column the view does not have (e.g. `math`) is refused with the parser's reason, not "Error executing tool". Only the `math` builder's parse errors are read so: an error in any other builder is not blamed on the operation.
- A failed run's message says what to do next: fix the step with `edit_transformation_step`, suspend it, or delete it.

### Added (mammoth-mcp-server 0.2.5)

- `list_tables` lists the tables of a database connection the project already has, so the user can ask "which tables are in my Postgres?" and Claude names a real table in its query. It lists the schemas first: with one schema, or none (MySQL, Redshift), the tables come at once; with several, Claude picks one. Mammoth reads the tables with the connector's own query, as its data page does. Some databases put the schema name straight into that query, so a schema Mammoth did not list is never sent.

### Fixed (mammoth-mcp-server 0.2.5)

- `list_connectors` with `connected_only` listed every connector. Mammoth filters by connections only when it counts them, and only within the page it read, so the tool now reads every page of connectors with their counts, keeps the connected ones and pages them itself, with `total` and `next_offset`.

### Added (mammoth-io 0.8.47, mammoth-cli 2.2.94, mammoth-mcp-server 0.2.7)

- `view transform convert-type`: `input_format_preference` also takes `strict` (an ambiguous day/month value becomes blank; a date whose day and month are equal converts). SDK `ConversionSpec` accepts it too.
- SDK `await client.resolve_workspace_id()`. SDK calls on a token client look the workspace up without blocking the event loop; a direct `client.workspace_id` read inside a running loop still works, blocks for that one lookup and logs a one-time warning.
- SDK `MammothClient(api_token=..., workspace_id=...)`: the workspace id is a hint that skips the lookup and sends no extra header.
- SDK `MammothClient(http_client=...)` sends through a shared `httpx.AsyncClient`. Credentials go on each request, never on the shared client; a pool shared between users should keep no cookies.
- New `.github/workflows/pr-checks.yml` runs the SDK, CLI and MCP checks (Python 3.12 and 3.14) on pull requests.

### Changed (mammoth-io 0.8.47, mammoth-cli 2.2.94, mammoth-mcp-server 0.2.7)

- CLI: a project-scoped command no longer asks `GET /workspaces/current` every time. The token's project pin is cached on disk for an hour; `doctor`, `auth status` and the 403 hint read it live, and `auth login` and `auth logout` clear it. `MAMMOTH_CLI_PIN_CACHE=0` turns the cache off. Credentials load once per process. Measured on `project list`: about 1.6 to 2.0s and one request, from 2.4 to 3.9s and two.
- CLI: command manifests ship pre-compiled as JSON. The CLI no longer writes a manifest cache to the user cache dir and removes the old `commands-*` files once.
- CLI: `commands/view.py` is split into a `commands/view/` package, loaded per command; names stay reachable as `mammoth_cli.commands.view.X`.
- SDK: Pydantic models build on first use (`defer_build`); importing the dashboard models takes about 0.26s instead of 0.40s.
- MCP server: tool calls share one connection pool instead of a new TLS handshake per call, and the pool closes when the server stops. Its User-Agent is now `mammoth-mcp-server/<version> mammoth-io/<version>`.
- OpenAPI spec re-pinned to production (728 operations); dashboard SDK and manifests regenerated.

### Deprecated (mammoth-io 0.8.47, mammoth-cli 2.2.94)

- `SupportAPI.connector_create` and `connector_update`: `price_per_month` is no longer sent (production removed it from connectors) and a non-zero value raises a `DeprecationWarning`. CLI `support connector create` and `update` add a `warnings` entry when the input carries it.

### Removed (mammoth-io 0.8.47, mammoth-cli 2.2.94)

- The legacy `mammoth-mcp` package, `bridge/`, the `mammoth-io[bridge]` extra and `publish.yml`. The hosted MCP server is `mammoth-mcp-server`.

### Release note (mammoth-io 0.8.47, mammoth-cli 2.2.94)

- `PipelineAPI.preview_task` refuses a `sample_size` outside 1 to 500 (the server's range) with `MammothValidationError`, and `view task preview` now forwards `sample_size`; before, the CLI dropped it and the server default always applied.
- `SupportAPI.workspace_list` reads every page; it stopped at the server's first 50 workspaces.
- `WorkspaceAPI.current` and `list` no longer look the workspace up first, which removed a duplicate `GET /workspaces/current` in the MCP server's token check.

### Added (mammoth-io 0.8.46, mammoth-cli 2.2.93)

- `view transform convert-type`: `conversions[]` items take `input_formats` (list), `output_format` and `input_format_preference` (`uk` or `us`); `format` stays as an alias.
- `view column format set`: sets a column's display format (date, number, currency, percentage) in one call.
- `view export download` saves a view as csv, xlsx, json, ndjson, xml, yaml or parquet (`format`; `view export csv` is unchanged). SDK: `ExportsAPI.to_file` and `to_file_url`.
- `view conditional-format replace`: deletes every rule and creates the given ones in one call. SDK: `conditional_format_replace`.
- `schema find` inlines the nested JSON Schema of non-scalar fields; input-validation errors carry `details.input_contract` (accepted fields and an example).
- `view data get` takes `columns` (display names) to return only those columns.
- `dataset batch-data` `columns` takes display names or ids, a list or one string (the route wants column ids); SDK `get_batch_data(columns=)` also takes a list.
- `dashboard v3 generate` accepts `intent`, `dataview_id` and `title` at the top level of `--input`.
- Condition operators: a regular-expression operator (`REGEX`, `RLIKE`, ...) is refused with the working alternatives.
- SDK `create_from_pdf` refuses a call the API would refuse (neither or both of `table_list` and `is_preview_needed`) with the reason; embedded `project_required` says how to pick a project.

## mammoth-io 0.8.45, mammoth-cli 2.2.92, mammoth-mcp-server 0.2.4 (2026-10-21)

Covers mammoth-io 0.8.24 to 0.8.45, mammoth-cli 2.2.46 to 2.2.92 and mammoth-mcp-server 0.1.1 to
0.2.4; each section names the version it shipped in.

### Added (mammoth-cli 2.2.92)

- `view transform sort` accepts `sort_by` as an alias of `order_by`, and an entry as a string (`"Revenue"`, `"Revenue asc"`, `"Revenue desc"`); `view transform limit-rows` accepts `limit` as an alias of `n` (both together are refused). `view transform batch` takes `split`, `unnest` and `pivot` steps (`unnest` and `pivot` replace the view's columns, so only as the last step, with no `sort` before them). A batch step can use the columns an earlier step adds (`split`, `copy-columns`, the `new_column` of `substring`, `extract-date` or `increment-date`).

### Fixed (mammoth-cli 2.2.91)

- `dataset list` with `names: true`: the bare `{id, name}` rows no longer each get an `unknown` `dataset_health` entry, which made a 114-name listing about ten times larger and cut it in an agent's chained call.

### Fixed (mammoth-cli 2.2.90)

- `dataset list`: the command contract (`schema get dataset.list`) now documents `names: true`, and a cut page's `note` says to use it, so an agent asked for a list of names no longer pages offsets.

### Added (mammoth-cli 2.2.89)

- `dataset list --input '{"names": true}'` returns up to 500 bare `{id, name}` rows of the project in one call (with `total`, and `more` when the cap cuts), so "which files can I see?" needs one call instead of a page per ~23 rows. The default shape is unchanged.

### Added (mammoth-cli 2.2.88)

- `dataset list` result carries `total`, the project's whole dataset count, so an agent counts datasets without paging. `project list` has no per-project count: the projects API returns none.

### Added (mammoth-io 0.8.45, mammoth-cli 2.2.87, changelog-analytics fixes)

- `dataset list` shows a URL dataset's link host as `source` (`url: HOST`), and `dataset refresh DATASET_ID --yes` fetches the link again into the same dataset and waits for the job (`DatasetsAPI.refresh_from_url`).

### Fixed (mammoth-io 0.8.45, mammoth-cli 2.2.87)

- `dashboard share` reports the share state it set (`{dashboard_id, share}`), and `dashboard delete` reads back the deleted board (`state.absent: true`) instead of the board list.
- `EmbedConfig` set sends only the fields passed; `get` explains the mode.
- Docs: a month bucket is `year_month_number`; auto-publish covers data refreshes only; sample a REST source with `connector ds-config create`, not `connection query`.
- Requires mammoth-io 0.8.45 (`DatasetsAPI.refresh_from_url` and the embed config set that sends only the fields passed).

### Added (mammoth-io 0.8.44, mammoth-cli 2.2.86: new backend endpoints; CLI commands for each)

- Exports: `ExportsAPI.runs(dataview_id, export_id)` lists an export's runs (`ExportRuns`, `ExportRun`); `ExportsAPI.rest_fill(dataview_id, docs_url)` asks the server to propose REST export settings from an API docs page and waits for the job; `ExportsAPI.export_hosts()` and `set_export_hosts(restricted, hosts)` read and replace the workspace's allowed export hosts (`ExportHostPolicy`, `ExportHostPolicyRead`). CLI: `view export runs`, `view export rest-fill`, `workspace export-hosts get/set`.
- `DataviewsAPI.summary(dataset_id, dataview_id)`: what a view has had done to it and where it goes. CLI: `view summary`.
- Workflows: `WorkflowsAPI.duplicate`, `undo_save` and `cancel_save_step`. CLI: `workflow duplicate`, `workflow save-undo`, `workflow save-cancel-step`.
- Email updates: `CollectionsAPI.email_updates`, `set_email_updates`, `my_email_updates`, `set_my_email_updates`, `send_test_email_update`, and the matching `DashboardsAPI.email_updates_*` methods. CLI: `dashboard email-updates list/get/set/me get/me set/test`, `collection email-updates get/set/me get/me set/test`.
- Live charts v3 and oEmbed: `DashboardsAPI.live_chart_list/create/get/audience/usage/placement` and `oembed`. CLI: `dashboard live-chart list/create/get/audience/usage/placement`, `dashboard oembed`.
- CLI: `dataset column-stats` and `dataset definition list/add/remove` are mapped to their backend operations in the manifests.
- The pinned OpenAPI spec is the live prod spec (651 operations); the release capability matrix keeps `master-20261002` as its baseline and lists the new routes as pending server release.

### Added (mammoth-cli 2.2.86, command and capability discovery)

- Did you mean: an unknown command names the nearest commands, including a nested group (`mammoth pipeline` -> `mammoth view pipeline`), and points to `mammoth how` / `mammoth schema find` instead of `schema get`; `details.did_you_mean` lists them and `recovery_commands` are ready to run. An unknown option names the nearest valid one (`--profle` -> `--profile`), and an option passed with its value as one argument (`"--project 3633"`, `--project3633`) says to pass the value separately. An unknown or wrong-case column (`Day` for `day`) names the closest column in the message, hint and `details.did_you_mean`.
- Allowed values in `--help` and in the error hint: an enum input field lists every value (it was cut at six, so `extract-date`'s `component` and `window`'s `function` hid most of theirs), and a fixed list inside a field gets an "Allowed values" line: `view transform batch` names its `steps[].op` list, and `dataset create` its `query_properties.data_pull_file` values. A refused batch op lists the allowed ops in `hint` (it was null) with `details.allowed` and `details.did_you_mean`. The help line, the hint and the check read the same tuple, so they cannot drift.
- `mammoth how "GOAL"`: turns a plain-language goal into an ordered recipe of commands. Each step has `command`, `command_id`, `purpose`, a runnable `example` (filled in with `--project` and an explicit `--profile`) and `key_flags`. Recipes cover refreshing on a schedule, appending a new file, blending two files on a key, upload to dashboard, a stuck upload, Power BI, CSV download, cleaning, sharing a dashboard and safe cleanup; they ship as `mammoth_cli/discovery/recipes.json`. A goal no recipe covers returns the `schema find` matches as steps with `matched: false` and a hint that says so. The bundled skill now starts with `how`.
- `mammoth capabilities` (also `mammoth schema find --unsupported [WORDS]`): what the CLI cannot do yet and what to do instead. Each entry has `area`, `limitation`, `instead`, `workarounds` (command and a runnable example) and `doc`. It lists file datasets that no automation can refresh, `schedule list`, editing a pipeline task through MCP (`view task update`), multi-project tokens and workbook imports built on synthetic data. The list ships as `mammoth_cli/discovery/limitations.json`; a test checks that every workaround is a real command.
- `mammoth skill show -o plain` (and `-o text`, a new alias of `plain` for every command) prints the skill file's markdown as it is, not one escaped JSON string; a terminal table prints it the same way. `-o json` is unchanged. The bundled `SKILL.md` front-matter `version` (it said 2.2.16) is stamped with the CLI version by `scripts/build_skill_catalog.py`, `skill show` stamps the running version, and a test keeps the two equal.
- `meta.next_commands`: after a main-flow command succeeds, one to three ready-to-run commands filled in with the result's ids: `file upload` -> `view data get VIEW_ID DATASET_ID` (or the dataset's own recovery command when it needs input), `view create` and every `view transform` -> `view data get`, `dataset file-settings update` -> `job wait`, `dashboard v3 generate` -> `dashboard get` and `dashboard figure add`, `dashboard figure add` / `figure-intent` / `chat edit` -> `dashboard get`, `automation create` -> `automation get`. Human output prints them as one `Next:` line on stderr. A write whose `verify` failed or is partial gets none. The map is `mammoth_cli/discovery/next_commands.json`. Each suggestion carries the `--project` and the explicit `--profile` the run was given, so running it as it is reaches the same project and workspace.
- `dashboard figure add` accepts `{"intent": "..."}` (optional `kind`), as the bundled skill says: it goes through the figure-intent route, where the server picks and draws the chart, and the result carries `route: "figure-intent"`. An exact `figure` with `dataview_id` works as before. Passing both, or neither, is a usage error whose hint shows both shapes and names `dashboard figure-intent`.

### Changed (mammoth-cli 2.2.86, command and capability discovery: behaviour changes)

- Lean success payloads. These commands now return a compact result by default: `dashboard figure add`, `dashboard figure-intent`, `dashboard v3 generate`, `dashboard chat edit`, `dashboard filter add`, `dashboard canvas save`, `dashboard canvas restore`. Each `canvas` becomes `canvas_summary` (`pages`, and each figure's `id`, `kind`, `title`, `page`); `plan` and `specs` are left out; null-only fields are dropped. Ids, checks (`figure_check`, `deliverable_check`, ...), `values`, `warnings` and `verify` stay, and `verify` is never trimmed. `compact.omitted` names what was left out and `compact.read_with` is the read that returns it. `--full` returns the old payload. (Not measured live: in the unit test a 12-figure canvas of about 15 KB, mostly nulls, comes back under 2 KB.)
- Envelope `meta` has a new optional field, `next_commands`, after a main-flow command succeeds; human output prints it as one `Next:` line on stderr.
- `--help` lists every value of an enum input field, joined with " | " (it was "a|b" and cut at six values).
- The unknown-command message now names the nearest commands ("Did you mean: ...?") and its recovery commands point to `mammoth how` and `mammoth schema find`, not `schema get`. The `unknown_option` and unknown-column hints changed to name the nearest option or column; `details.did_you_mean` is new.

### Changed (mammoth-cli 2.2.86, speed)

- One service per command run: the handler, its verify step and its `state` read-back share one client and connection (each new client cost a new TLS handshake and token lookup, about 0.5 s). Job and pipeline waits are rebound per opener.
- Reads before a write are made together and once: the view record and the exports listing are fetched in one round trip and handed to the impact check, row count and type check, which each fetched the view again. The row count and the pipeline state after the write are read together.
- The `state` block of a view write takes its columns and row count from the data read instead of a separate `view get` (which also listed every dashboard in the workspace).
- A no-op `convert-type` (every column already has the type) no longer re-reads exports or samples rows: it decides from the view record it already has, and its `state` is the columns and row count with `unchanged: true`.
- `dataset delete` verifies with the one targeted read it already makes and returns `deleted: [id]`; it no longer lists the project's remaining datasets.
- `dashboard v3 generate` / `chat edit` read the canvas once for the check and the board's numbers.
- Startup: the `mammoth` entry point turns off pydantic's plugin discovery (`PYDANTIC_DISABLE_PLUGINS=__all__`, unless already set). pydantic looked up every installed plugin the first time it built a model and imported each one; with logfire installed beside the CLI that was about 0.4 s on every command that loads the SDK (`auth status` 0.87 s -> 0.44 s, `view transform filter --help` 1.01 s -> 0.62 s).
- `view list` without a dataset id reads the views of 5 datasets at a time instead of one after another (folded in from #177). The result, its order, `datasets_visited` and `next_dataset_offset` are unchanged; a walk that stops early still never reads the waves after it.
- The keyring backend cache loads `importlib.metadata` only when it reads or writes its record, not at import (folded in from #177).
- Requires mammoth-io 0.8.44 (the new endpoints' SDK methods and the 60 s fast job poll).

### Changed (mammoth-io 0.8.44, speed)

- `jobs.wait_for_job` / `wait_for_jobs` keep polling at `poll_interval` (2 s by default) for the first 60 seconds of a wait, not 10, before the gap rises to 5 s. A typical upload or transform job finishes in 15-30 s, and the 5 s gap added up to about 3 s to each one (an upload of 30 rows went from 25.0 s to 21.8 s in the CLI's measurement).

### Fixed (mammoth-cli 2.2.86, team bug bash 2026-10-15)

- `mammoth how` handles a goal with several parts ("blend user events with docs by day and build a dashboard that refreshes daily"). It used to match no recipe and fall back to unrelated commands. Now each part (split at "and", "then", commas) gets its recipe, the recipes run in pipeline order (load, blend, clean, dashboard, share/export, schedule), and their steps form one list with the upload first and once. The result names each part's recipe in `recipes`. Verb forms ("refreshes", "joined") match their recipe words.
- `auth login --server-prefix ''` (or any malformed prefix) reports `invalid_server_prefix` first; a non-interactive run said "needs --device" instead.
- Human-mode usage errors (`-o table`/`plain`) print Click's `Usage:` line again above the error, as before the did-you-mean change.
- A view write's `state` block reads `view get` when the data read came back without the view record, instead of showing no columns and a null row count.
- `dataset list` (and the name search) report a real `dataset_health` for every dataset. The list route already returns `status`; the compact summary dropped it for a ready dataset, so every row read `unknown` with a "run mammoth dataset get" hint. Each row now carries `status` (about 18 characters a row); no extra request is made, so big projects list as fast as before.
- `file upload`: the `dataset_health` entry carries the dataset's `name` (it was `null`), and each uploaded dataset in `datasets` has a `name`.
- Workspaces and projects are named beside their ids: `auth login` says "Signed in to workspace Filipe Silva (519), project Sales (4460)" and adds `workspace_name` / `project_name`; `auth status --check` adds `workspace_name` and `token_project_name`; the "token is limited to project" errors and the `project list` / `project get` notes name the pinned project. A failed name lookup falls back to the id and never fails the command.
- `auth status` (and `auth login`): `expires_at` is the access token's expiry, not the login's. It is kept, and `access_token_expires_at`, `refreshes_automatically: true` and `expires_at_note` say what it means. Documented in the bundled skill (`machine-output`, `auth`) and `docs/authentication.md`.
- Discovery: `schema find` ranks `folder.*` for "folder", "create/make/rename a folder" and "move a dataset into a folder", `file upload-folder` for "upload a folder of files", and `dataset delete` beside `file delete` for "delete an uploaded file". `mammoth --help` now says what `file` and `folder` are for (a folder is a project folder; an uploaded file becomes a dataset).
- A follow-on job (view create/export/etc.) that outlives `--job-timeout` reports `execution_state: unfinished` with `mammoth job wait JOB_ID` (outcome `pending`, exit 0), not `job_failed`.
- `dashboard import-workbook` with the backend's `fitted_sample` data is `partial` (exit 3) with `synthetic_data`, row counts expected (CSV records in the `.twbx`, so a quoted line break is one row) vs received, and how to load the real data. `dashboard chat edit` with `changed: false` says "NOT APPLIED" (the model's own text moves to `model_message`) and a refused measure suggests `dashboard figure add`; refusal notes no longer swallow the next paragraph or repeat.
- `file upload` with `append_to_ds_id` reports the target dataset (`dataset_id`, `rows_before/after/added`, `staging_dataset_ids`), not the staging copy. A mixed multi-file upload (some ready, some `error` or refused) is `partial` (exit 3) with each failed file's reason; `dataset_health` reads backend status `error` as `failed` with the backend's reason.
- `schedule create` and a 4AUTO006 backend refusal explain that a file-backed dataset cannot be scheduled and point at `file upload` with `append_to_ds_id` (`dataset_not_refreshable`, exit 2).
- A pinned token refused in another project says "This token is limited to project NAME (ID)" and how to use `--project`; help types keep their brackets (`list[ColumnNameMapping]`); `view task list` page 1 says `offset: 0`.
- A dataset in `need_action` is pointed at `dataset file-settings get/update` (not `dataset interpretation preview`, which answers 4DSET066 without a report, and not `view create`); the `file-settings update` example uses `initial_skip_count: 0`. `dataset list`/`dataset find` say `need_action` for a held file, as `dataset get` does.
- `dataset bulk-delete` and `folder delete`/`bulk-delete` verify and report each id (`deleted`, `not_found`, `failed`): all good exit 0, some `partial` exit 3, none deleted exit 5 (all not found) or 1. They returned `data: null` and exit 0 for ids that never existed.
- `-o yaml` errors are YAML envelopes; `-o csv` writes `dataset list`, `view list`, `file list` and `folder list` rows.
- `file upload` with no path is `missing_argument` (exit 2, not `internal_error`); a directory says to use `file upload-folder`; a second path says to use `--input '{"files": [...]}'`. `file list`/`folder list` drop the raw `next` API URL and null `total` for the `paging` block.
- `view transform convert-type` TEXT to NUMERIC/DATE warns that unparsable values (such as N/A) become empty, naming each column once.
- Unknown dataset/file ids (4DSET001, 4FILE001) are `resource_not_found` (exit 5). Job recovery commands keep `--project`. `auth status --profile NAME` for a profile that does not exist exits 4 with `mammoth auth login --profile NAME`. `dataset rename` to the current name is a no-op success. An export target that is a directory is refused before the export job starts.

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

### Added (mammoth-mcp-server 0.2.4)

- The user can bring data in from a database or an app over MCP. `list_connectors` lists the sources Mammoth connects to, and which the workspace's plan includes. `connect_source` gives the user the page in Mammoth that opens "Add data" on that connector in the project; they sign in to the source and pick the data there, so no credential passes through the model. `find_new_datasets` then reports the datasets the caller added to the project, with each one's view and link; a teammate's dataset made in the same time is left out (Mammoth records the maker by name), as `check_upload` does for a file. All three are read-only: the change is the user's own, in Mammoth.
- Only a project admin may connect a source, so `connect_source` checks the user's role on the project first. Anyone else gets no link, and `next_step` says who can connect it.
- A client with MCP Apps draws a "Connect <source> in Mammoth" button under `connect_source`, which opens the page through the host. A client without MCP Apps shows `mammoth_url` as before. The link carries `from=assistant`, so Mammoth's data page can tell the user to go back to the chat once the data is added.
- Connecting a source makes a connection, and that takes the user two or three minutes in Mammoth. `connect_source` now starts a five-minute watch for the new connection and returns its `watch_id`. `find_new_connection` reports the connection as soon as it is made: each call waits up to 20 seconds, looking every 10, and says `waiting` (call again) or `gave_up` once the five minutes are over. The connect button keeps calling it for the whole watch, and tells the chat when the connection is made. `find_new_datasets` waits the same way for what the user brings in through it.
- Once a project has a database connection, data comes in through it without leaving the chat. `list_connections` lists the project's connections to a source. `preview_query` runs a query on one and returns the first rows, and `add_dataset_from_connection` makes a dataset from that query and reports at once when Mammoth refuses it. It pulls once, now, unless asked to repeat every so many hours, days, weeks or months (`repeat`, `every`, `start_at`, `until`); a refresh replaces the rows, adds the new ones, or combines them on a unique column (`on_refresh`). A client with MCP Apps draws a form under `preview_query`: the first rows, with the name, the query, the schedule and the refresh filled in, and one button that makes the dataset and tells the chat. Without it, the client is told to ask all three in one message, never one by one. Both send SQL to the user's own database, which Mammoth does not make read-only, so they are marked destructive and refuse a query that does not start with SELECT or WITH, that holds a second statement, or that names a word that writes (such as DELETE in a CTE, or SELECT ... INTO). A query with a backslash, a `$$` dollar quote or a comment (`--`, `/* */`, `#`, `//`) outside a string is refused too, and so is a `[name]` on SQL Server, because databases read these differently and each can hide SQL from the check. The check is a guard, not a parser: a function that writes, such as Postgres's `dblink_exec`, still passes, and the connection's database account decides what a query may change. Postgres, MySQL, SQL Server, Redshift, Snowflake, Databricks, SAP HANA and BigQuery are supported.
- `connect_source`, `find_new_connection` and `find_new_datasets` record the connector key, whether it got connected and how many datasets came in, so we can see which connectors people use. The key is a name from Mammoth's own list of connectors, and no other argument is recorded.

### Added (mammoth-mcp-server 0.2.3)

- `aggregate_data` has Mammoth work out totals, counts, averages, lows and highs over a view, for the whole view or by group (a date grouped by day, week, month, quarter or year). It is read-only: it adds nothing to the view's pipeline, and a read-only connection may run it. Columns are named as the user sees them.
- `get_dashboard` reports `values`: each KPI card's number and each chart's first rows, with the period and filters it counts under, as Mammoth evaluated them. A published board's numbers are its published version's, the one its share link opens; an unpublished board's are the draft's. `values_from` says which. `include_values=false` skips them for a quicker read. A dashboard on the older engine, or one Mammoth cannot evaluate, reports `values_unavailable` with the reason instead; the read itself does not fail.
- Views, datasets, pipeline results and a ready uploaded dataset carry `mammoth_url`, the page in Mammoth they open on. The server tells the client to give the user that link.

### Changed (mammoth-mcp-server 0.2.3)

- `aggregate_data` refuses a `limit` below 1.
- `aggregate_data` leaves out the `hash` row identity, returns a date group as a valid ISO time (Mammoth sends `+00:00Z`), and, when ranked, says the rows are the top groups by that result.
- `get_data` no longer returns the `hash` row identity Mammoth adds to every row. It is no column of the user's, and Claude read its values as duplicate rows.
- The server and `get_data` tell the client to take every number from `aggregate_data` or a dashboard's `values`, and never to add up rows itself.

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
