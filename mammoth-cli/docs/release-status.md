# CLI release provenance

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

PYPI_HASHES_PLACEHOLDER

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
