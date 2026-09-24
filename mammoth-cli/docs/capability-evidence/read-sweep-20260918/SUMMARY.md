# Read-only capability sweep — Mammoth CLI vs release environment

171/171 read commands from `targets.json` executed exactly once via the `ro-mammoth`
fence (release profile, JSON output, `--no-input`, `--timeout 60`). Results in
`results.jsonl` (one JSON object per command). Fixtures used: workspace 4, project 3
("API Tests_project"), datasets 28/29/30/31/33, views (33→49,43; 31→48,41; 30→47,40;
29→46,39; 28→45,38), dashboard 48, user 5, batch 33 (dataset 33), task 3 / version 3
(view 46, dataset 29), job 233 (an AI-suggestion job id, the only job id discoverable
read-only), connector key `bigquery` (present in `connector.list` but not added).

## Verdict counts

| verdict | count |
|---|---|
| ok | 89 |
| blocked_missing_fixture | 40 |
| cli_error | 17 |
| ok_empty | 6 |
| fence_denied | 6 |
| server_error | 5 |
| validation_error | 5 |
| not_supported | 2 |
| authorization_error | 1 |
| **total** | **171** |

## validation_error (400/422 — bug candidates, backend message verbatim)

- **ai.suggestion.list** (`ai suggestion list --project 3`) — 400 "Validation error" (no further detail surfaced).
- **schedule.list** (`schedule list --project 3`) — 400 **"Not implemented"**. A 400 status paired with an "Not implemented" message is itself a mismatch — that's normally a 501/404 signal, not a validation failure.
- **ai.sql.generate** (`ai sql generate "show total sales by month" --project 3`) — 400 "Validation error".
- **view.ai.generation-info** (`view ai generation-info 49`) — 400 **"Not implemented"**, same status/message mismatch pattern as `schedule.list`.
- **connector.get** (`connector get bigquery`) — 400 **"Invalid connector key"**, even though `bigquery` is literally one of the 42 `name_key` values returned by `connector.list` (sample: azure_blob, bigquery, databricks, dropbox, facebook_ads, …). This is a binding mismatch between `connector.list`'s output and `connector.get`'s accepted input.

## cli_error (CLI/SDK failed before or while parsing the request/response — bug candidates)

- **webhook.list** — `api_error`, "The Mammoth operation failed unexpectedly." (no status code recorded; profile-scoped, no project needed).
- **external-key.list** — `not_authenticated`, "No Mammoth credentials are available for this command." (odd for an authenticated release-profile session that succeeds everywhere else).
- **job.get-many**, **job.wait-many** — both require the `job_ids` field, but the command exposes **zero** CLI options or positionals (`options: []`, `positionals: []` per `schema get`) — the field cannot be supplied through the CLI at all, regardless of whether a job id is known.
- **template.list** (workspace templates, `--project 3`) — backend returned **HTTP 200** (success) but the CLI/SDK still raised `api_error` — a response-envelope/shape mismatch; the request objectively succeeded server-side.
- **dashboard.style.default.get** (`--project 3`) — client-side `ValidationError` with no endpoint/status_code recorded at all — looks like the CLI/SDK's response model doesn't match what the backend actually returns.
- **project.publish-credentials 3** — requires `odbc_type` input field; no discoverable value read-only, but the field name at least is exposed as a real body field (not a total dead end like below).
- **project.resource-dependencies** (`--project 3`) — requires `resource_ids`, but only `project_id` is exposed as a positional; `resource_ids` has **no CLI option at all**. Command is unusable via CLI in read-only/no-input mode.
- **browse.folder 0** (`--project 3`) — rejected with `'folder_id' must be a positive integer, got 0`, yet `folder.root` reports the root folder's own `id` as `0`. The CLI's own root-folder id fails its own positional-arg validation.
- **view.conditional-format.list 49 33** — failed once with `not_authenticated` ("No Mammoth credentials are available") inside a 20-command batch; an immediate manual retry with identical arguments succeeded (`data: []`). Looks like an intermittent/flaky auth failure under concurrent or rapid-fire command load, not a deterministic routing bug.
- **view.pipeline.items-all 49 33** — schema lists `dataset_id` as an optional second positional (`DATASET_ID`), but supplying it (`view pipeline items-all 49 33`) still errors `This command requires the 'dataset_id' input field.` — the documented positional isn't actually wired through.
- **dashboard.data.draft 48**, **dashboard.data.published 48** — both require `sql`, exposed nowhere in CLI options/positionals (`options: []`). Undocumented/unusable without `--input-file` (which the sweep fence blocks, and which isn't offered as a flag either).
- **dashboard.og-card 48** — backend returned **HTTP 200** but a non-JSON body (`exception_type: JSONDecodeError`); the endpoint likely returns binary image data and the CLI's JSON parser chokes on it.
- **dashboard.template.get sales-performance** (a real template id from `dashboard.template.list`) — client-side `ValidationError` parsing the response; response-shape mismatch, not a bad request.
- **dashboard.rls.value.list 48** — requires `column`, but there is **no CLI option for it at all** (`options: []`); `--column Entity` is rejected as `Unknown option`. Command is completely unusable via the CLI.
- **connector.ai.session.list** (`--project 3`) — backend returned **HTTP 200** but CLI raised `api_error` — same response-envelope mismatch pattern as `template.list`.

## not_supported (404/405/501)

- **addon.list** — 404 "The requested Mammoth resource does not exist." (route appears to not exist at all in this environment).
- **workspace.user.get 5** — 405 (method not allowed) even though `workspace.user.list` returns the same user id 5 with full detail — the singular `get` route looks unimplemented/misrouted server-side.

## server_error (5xx)

- **dashboard.source.list**, **browse.root**, **browse.project** (`--project 3`) — all 500 "Mammoth returned an API error." with no further backend detail exposed.
- **activity.export** — 500, "The request may have committed, but its outcome was not confirmed." (exit 7/retryable class).
- **connector.connection.list bigquery** (`--project 3`) — 500, for a connector that is listed but not added/configured; arguably should be a clean empty list or 4xx rather than a 500.

## authorization_error

- **client-app.list** — 403 "Cannot access this API with API-tokens" (an API-token-vs-cookie-auth scoping restriction, consistent/expected rather than a bug).

## fence_denied (correctly refused by the read-only fence per hard rules)

`auth.status`, `config.list`, `config.path`, `config.get`, `context.project.status`,
`completion.show` — all in the off-limits `auth`/`config`/`context`/`completion`
local families per the sweep's hard rules; the wrapper denied them mechanically
before any request could be made. No workaround attempted, as instructed.

## blocked_missing_fixture (40 total) — needed an id/fixture unobtainable read-only

Grouped by cause:
- **Empty parent list → no id to test with `.get`/`.dependencies`**: `automation.get`, `parameter.get`, `parameter.dependencies`, `snippet.get`, `snippet.dependencies`, `workflow.get`, `file.get`, `folder.get`, `dashboard.qa.session.get`, `agent.session.messages`, `data-app.get`, `data-app.active-job`, `data-app.job`, `data-app.pipeline-changes`, `data-app.user.list`.
- **Parent list itself errored, so no id was ever recovered**: `webhook.get` (list cli_error), `external-key.get` (list not_authenticated), `client-app.get` (list authorization_error), `schedule.get` (list said "Not implemented"), `template.get` (workspace-level list had the 200-but-api_error binding bug).
- **No connectors added/connected in the workspace** (`connector.list` shows `is_added: false` for all 42 entries): `connector.ai.history`, `connector.ai.session.messages`, `connector.connection.get`, `connector.ds-config.get`, `connector.ds-config.list`, `connector.query.generate`, `connector.query.status`.
- **No such resource exists anywhere sampled** (checked view 49/dataset 33 and view 46/dataset 29 — the only view with real pipeline task/version history): `view.checkpoint.get`, `view.data-check.get`, `view.export.get`.
- **Dashboard 48 was never published** (`was_published: false`, the only dashboard in the workspace): `dashboard.published.canvas`, `dashboard.published.og-card`, `dashboard.published.pdf-artifact`, `dashboard.published.share-page`, `dashboard.published.video-artifact`.
- **No real job of the right type discoverable read-only** (only job id found was 233, an AI-suggestion job, wrong type for these): `dashboard.job-by-url`, `dashboard.pdf-artifact`.
- **Requires a full structured body, not an id** (would need `--input-file`, which the sweep fence blocks): `view.task.preview` (needs `task_spec`).
- **Requires a local binary fixture file that doesn't exist**: `dashboard.assess-pbix`, `dashboard.assess-twb`.

## Surprising response-shape observations

- **Two distinct "the backend actually succeeded (HTTP 200) but the CLI still reports an error" cases**: `template.list` and `connector.ai.session.list`. Both point at a client-side response-model/envelope mismatch rather than a real backend failure — worth checking the corresponding SDK response models against what `/workspaces/{id}/templates` and the connector AI session-list endpoint actually return today.
- **Two "400 status code but message says Not implemented" cases**: `schedule.list` and `view.ai.generation-info`. A feature-not-implemented condition is being surfaced as a validation error rather than 404/501, which will confuse any caller branching on status code.
- **`dashboard.og-card`** returns a non-JSON (likely binary image) body with status 200, but the CLI unconditionally tries to JSON-decode responses — this will break for every non-JSON-returning route, not only this one.
- **Several list-vs-get id mismatches**: `connector.get` rejects a connector_key that `connector.list` returned; `workspace.user.get` 405s for a user id that `workspace.user.list` returns cleanly; `browse.folder` rejects folder id `0`, which is exactly the id `folder.root` reports for the root folder.
- **At least four "read" commands have required body fields with zero corresponding CLI surface** (no positional, no option): `project.resource-dependencies` (`resource_ids`), `dashboard.data.draft`/`dashboard.data.published` (`sql`), `dashboard.rls.value.list` (`column`), `job.get-many`/`job.wait-many` (`job_ids`). These commands are structurally unusable from the CLI today, independent of what fixtures exist.
- **One likely flaky/intermittent auth failure**: `view.conditional-format.list` failed with `not_authenticated` once inside a large sequential batch, then succeeded immediately on manual retry with identical arguments.
- **Envelope shape is consistent between list and get** across all working commands: every successful response wraps its payload in `data` (dict or list), with `meta.command`/`meta.profile`/`meta.workspace_id`/`meta.project_id` always present; pagination-style lists nest under keys like `items`/`datasets`/`files`/`folders`/`tasks` etc. rather than a uniform key name, so callers must know each resource's specific wrapper key name.
