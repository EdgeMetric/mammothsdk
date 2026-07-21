# Audit, notes, blockers, and TODO ledger

The primary agent updates this file after each accepted commit. Worker agents do
not edit it.

## Decision record

| Decision | Locked value |
|---|---|
| Coverage authority | Production OpenAPI operation inventory |
| Inspected operation count | 376 |
| Inspected SDK method count | 242 |
| Missing platform operations | Extend typed SDK first |
| Feature state | Production operations only |
| CLI distribution | Separate `mammoth-cli` package |
| Executable | `mammoth` |
| Mammoth transport | Public `mammoth-io` only |
| Required authentication | API key, API secret, workspace ID |
| Optional authentication | Server prefix |
| Default server prefix | `app-eu` |
| Default URL | `https://app-eu.mammoth.io/api/v2` |
| Project handling | Saved context plus explicit override |
| Credential modes | Keyring, explicit file fallback, or environment |
| Input | Typed flags plus strict JSON/YAML |
| Output | Table, JSON, YAML, NDJSON, plain |
| Systems | Linux, macOS, Windows |
| Python | 3.12 through latest stable; 3.10-3.11 unsupported |
| Primary development Python | 3.14.3 |
| Current CI Python matrix | Latest patches of 3.12, 3.13, and 3.14 |
| Live tests | Dedicated test tenant |
| Skill | Bundled, CLI-installable Codex/Claude/Cursor skill |
| Writing | ASD-STE100 Issue 9-based house profile |
| Target branch | `add-cli-for-mammoth` |

## Self-audit findings and fixes

### SDK parity was incorrectly treated as Mammoth parity

Finding: The SDK has 242 audited methods. The production OpenAPI has 376
operations and major additional resource families.

Fix: Make the OpenAPI inventory authoritative. Give all OpenAPI operations a
reviewed disposition. Extend the typed SDK before adding missing commands.

### Authentication included unrelated context in early drafts

Finding: Project, base URL, and timeouts were previously described near login.

Fix: Login requires only key, secret, and workspace. Server prefix is optional.
Project and base URL remain operational configuration.

### The plan did not initially specify every structured operation

Finding: A name-only command list cannot define `bulk_replace`, exports,
conditions, pipeline patches, or other nested requests.

Fix: Require an exact command-spec record for every command. Block handlers
until its request model, examples, safety, SDK call, and tests are approved.

### TDD originally started too late

Finding: Per-handler tests alone could miss entire resource families.

Fix: Generate OpenAPI and SDK inventories first. Write red parity and
registration tests before handlers.

### Public SDK methods use private helpers

Finding: View resolution, exports, publishing, and SQL generation use private
cross-subclient or client request methods.

Fix: Add public typed SDK seams. Prohibit private SDK calls from CLI source.

### Draft state is not safe across CLI processes

Finding: `View.is_draft_mode` uses process-local state.

Fix: Add a server-backed typed draft state and standardize on
`enter|submit|discard|exit`.

### Pagination metadata is often lost

Finding: Several SDK list methods discard envelopes or do not accept an offset.

Fix: Add typed pages. Offer `--all` only after a proven continuation contract.

### Asynchronous behavior is inconsistent

Finding: Some methods always wait, some return jobs, and some hardcode timeouts.

Fix: Record wait policy per operation and add typed start/wait results before
offering `--no-wait`.

### Secret fields are not consistently modeled

Finding: Connectors, exports, keys, client apps, webhook URIs, and passwords can
leak through raw dictionaries.

Fix: Add explicit secret metadata, approved transports, recursive redaction,
and leakage tests for all output modes.

### Some destructive API shapes are unsafe or unclear

Finding: Dataset bulk delete has no visible IDs; conditional-format delete can
remove all rules; folder deletion removes contents by default; addons can
affect billing.

Fix: Verify OpenAPI and live contracts, use accurate command names, and apply
exact high-impact confirmation.

### Quick installers introduce supply-chain risk

Finding: Piping a mutable script to a shell reduces review.

Fix: Publish versioned release assets, checksums, provenance, pinned tool and
CLI versions, plus a download-and-verify installation path.

### Formal ASD-STE100 compliance cannot be claimed

Finding: The official standard and dictionary are copyrighted, and house
checks do not provide certification.

Fix: Use a named house profile, cite the official standard, and combine Vale
checks with human review. Do not claim certification.

### Concurrent agents can conflict

Finding: Agents share one repository filesystem.

Fix: Use isolated worktrees, focused commits, non-overlapping ownership, and
primary-agent integration.

### The plan claimed completion before the parity freeze

Finding: Earlier wording called the specification complete although the 376
OpenAPI dispositions, 242 SDK records, and exact command manifests are the
first required work products.

Fix: Call this deliverable the audited implementation plan. Define a pre-code
specification freeze, give it exact paths and schemas, and prohibit production
handlers until the primary agent reviews every record and the central tests are
red for the expected reasons.

### Auth, installers, skills, and worker packets lacked exact contracts

Finding: Earlier phases named outcomes but left profile commands, release
assets, installer rollback, agent skill paths, and worktree integration to
workers.

Fix: Add normative auth/live and packaging/install/skill documents. Lock command
syntax, paths, ownership, platform support, test IDs, and worker base-SHA rules.

### The live OpenAPI output is nondeterministic

Finding: Repeated 2026-07-21 fetches kept 234 paths and 376 operations but
changed raw and canonical digests. Differences included generated examples, a
project-color default, parameter order, and an unrelated schema description.

Fix: Pin the exact raw snapshot. Generate a normalized contract projection for
review, but never let CI refresh from the network or silently discard semantic
changes. Require primary review for every snapshot update.

### The first catalogs left two ambiguity classes

Finding: The first resource appendix exposed low-level dataset IDs in view
commands and used separate bulk-delete and nested dataset-batch spellings.
The AI and top-level client methods were inventoried but lacked reviewed
command dispositions. The typing-only `ViewHost` methods also counted in the
SDK inventory without explicit alias records.

Fix: Make `VIEW_ID` the user-facing view target and resolve its dataset through
a public typed SDK seam. Standardize on `view delete VIEW_ID...` and top-level
`batch list|get`. Add reviewed dispositions for all six `AIAPI` methods, all
five `MammothClient` convenience methods, and both `ViewHost` protocol aliases.
Plans 09, 10, 11, and 14 now account for all 242 inventory rows.

### Autonomous agent use was not initially a testable gate

Finding: JSON output alone does not let a low-context agent discover inputs,
recover from timeouts, or continue work without source inspection.

Fix: Require `--no-input`, capability and schema discovery, stable result and
error envelopes, exact recovery commands, resumable job/resource identity, and
low-context forward tests. A worker must treat these as release gates, not
documentation preferences.

## Normative current state

- The branch was created from clean `main` on 2026-07-21.
- The branch base is `071092b286a51eced4f85e536f1b0c70f400ea7f`.
- The plan set is the first intended branch change.
- The production OpenAPI URL is public and returned OpenAPI 3.1.0.
- The inspected OpenAPI root declares `apiKey` and `apiSecret` as separate
  security alternatives. OpenAPI array semantics imply OR, but the product and
  SDK require both headers. Treat this as an OpenAPI defect and test both.
- Workspace and project IDs remain path/header context where required.
- The current SDK defaults to `app.mammoth.io`; the CLI default must derive
  `app-eu.mammoth.io` without silently changing unrelated SDK consumers.
- The current SDK transport is synchronous `requests`. The CLI must reflect
  actual synchronous behavior.
- The current SDK owns a `requests.Session` but has no public `close()` method.
  Add deterministic close and context-manager support before CLI integration.
- The MCP package is a useful behavior reference but contains stale wrappers.
  It is not a parity authority.
- The transformation manifesto documents capabilities that must be reconciled
  with production OpenAPI operations. Do not create commands for planned-only
  features.
- The authorized development target is `https://release.mammoth.io/api/v2`,
  normalized as server prefix `release`, with workspace ID `4`.
- The supplied credentials are for live development tests. Keep them only in
  the ignored local `.env.plan`; do not copy their values into tracked files,
  logs, snapshots, command lines, or artifacts.
- Every recon and live-test run must create and use a new isolated project. It
  must not mutate an existing project.
- The supplied credentials are verified for authentication and project
  create/list/delete. Dataset creation, file upload, view operations, and
  transformations are authorized in the pre-existing provisioned project `180`
  ("Test") but NOT in freshly API-created projects (project-scoped RBAC; see the
  recon log and blockers). Run those families' live acceptance against `180`,
  creating and cleaning up only own resources. Do not yet claim the full
  acceptance suite passed until those handlers exist and their live tests run.
- The reviewed planning appendices contain exactly 376 OpenAPI operation rows
  and 242 public SDK method rows. They are planning evidence; the generated
  pre-code manifests and their primary sign-off remain implementation work.
- All fifteen plan documents have resolvable relative links. The ignored
  `.env.plan` has mode `0600` and exactly the four authorized variable names.

## Historical recon log

| Date | Target | Action | Result | Created | Cleanup |
|---|---|---|---|---|---|
| 2026-07-21 | `release`, incorrect workspace `2` | Connect | `Invalid token` | None | Not needed |
| 2026-07-21 | `release`, workspace `4` | Connect, create/list/delete project | Passed; project/list response shapes recorded | Project `1193` | Deleted |
| 2026-07-21 | `release`, workspace `4` | Create project, upload `employee.csv` | Upload not authorized | Project `1194` | Deleted |
| 2026-07-21 | `release`, workspace `4` | Create project, create sketch dataset | Dataset create not authorized | Project `1195` | Deleted |
| 2026-07-21 | `release`, ws `4`, project `180` ("Test") | Get project, list datasets, create + delete sketch dataset | All passed; dataset `2340` created and deleted | Dataset `2340` | Deleted |
| 2026-07-21 | `release`, ws `4`, fresh project `1196` | Create project, create sketch dataset | Project create passed; dataset create returned `MammothAuthError: You are not authorized to perform this action` | Project `1196` | Deleted |
| 2026-07-21 | `release`, ws `4`, project `180` | CLI `project list/get/pending-changes/resource-status` (read-only) via `python -m mammoth_cli.app --output json` | All exit 0 with valid `{schema_version,data,meta}` envelopes; `get 999999999` returns stderr error envelope, exit 1 | None | Not needed |
| 2026-07-21 | `release`, ws `4` | CLI `project create` → `delete` (guard verification) | create exit 0; `delete` without `--yes` (json) exit 2 `confirmation_required`; `delete --yes` exit 0; `update` on fresh project exit 4 `authentication_failed` (server RBAC) | Project `1197` | Deleted |

## Blockers before live acceptance

- [x] Store the supplied test credentials in the ignored local `.env.plan`.
- [x] Record the allowlisted test workspace ID as `4`.
- [x] Record the test server prefix as `release`.
- [x] Verify that the credentials can create and delete an isolated project.
- [x] Root-caused the earlier "dataset create not authorized" result on
  2026-07-21. It is **project-scoped authorization**, not a principal-wide
  limitation. Confirmed live: creating a sketch dataset in a freshly
  API-created project (`1196`) returns `MammothAuthError` ("You are not
  authorized to perform this action"), but the same operation with the same
  credentials succeeds in the pre-existing provisioned project `180` ("Test").
  The API principal that creates a project is not automatically granted
  dataset-write authority on it (project-level RBAC / data-domain
  provisioning). Both recon runs cleaned up fully (dataset `2340` and project
  `1196` deleted; no leaks).
- [x] Live target for dataset/view/pipeline/transformation acceptance is the
  user-authorized pre-existing project `180` on `release` workspace `4`. Live
  tests MUST create their own datasets/views inside `180` and delete only what
  they create; they MUST NOT touch its pre-existing datasets ("Result Dataset",
  "Multi-Store_Retail_Sales.csv", "Multi-Store_Retail_Sales.csv 2",
  "Supply_Chain_Optimization.csv"). This is an explicit, user-authorized
  exception to the "always create a new disposable project" rule, because the
  principal cannot create datasets in self-created projects.
- [ ] Re-run isolated dataset, view, query, pipeline, and bulk-replace live
  acceptance against project `180` as each family's handlers land (Phases 4-7).
- [ ] (Optional) Ask whether the principal can be granted dataset-create
  authority on self-created projects, to restore the disposable-project
  discipline. Not required while `180` is authorized.
- [ ] Record available external export and connector fixtures.
- [ ] Add dedicated disposable fixtures for billing, account, user, and
  external-destination tests if those tests are authorized.

## Decisions deferred until publication, not implementation

- [x] Confirm that the `mammoth-cli` PyPI project returned 404 on 2026-07-21.
- [ ] Recheck and reserve the `mammoth-cli` PyPI project during an authorized
  publication workflow.
- [ ] Configure PyPI trusted publishing.
- [ ] Decide whether a custom install domain will replace GitHub release URLs.
- [ ] Authorize publication and GitHub release creation.

## Implementation ledger

Append one row after each accepted change.

| Date | Commit | Phase | Operations/commands | Tests | Reviewer notes |
|---|---|---|---|---|---|
| 2026-07-21 | `bb2557f` | Phase 0: audited plan | 376 OpenAPI inventory rows; 242 SDK inventory rows; command catalogs and implementation gates | Planning link, uniqueness, catalog-accounting, formatting, and secret-value scans passed | Primary self-review completed; implementation has not started |
| 2026-07-21 | Phase 1 commit | Phase 1: parity freeze + red-first tests | `mammoth-cli/` package scaffold; pinned OpenAPI snapshot (376 ops); generated 376-op operation manifest (364 command, 11 protocol_only, 1 alias), 242-method SDK manifest (184 command, 54 alias, 4 reviewed SDK-only exemptions), 435 command records, schema-v1, parity report | 45 contract tests; 31 green (parity/schema/introspection/examples/source-guards), 14 red as expected (232 planned SDK symbols + 4 SDK-foundation gaps for Phase 2, 9 runtime tests for Phase 3). Reproducible build verified; strict mypy/ruff/black clean on package | Primary review complete; the red baseline is recorded in `spec/reports/expected-red-report.md`; no manifest/inventory defects |
| 2026-07-21 | Phase 2/3 commit | Phase 2 typed SDK API groups + Phase 3 CLI runtime core | Added 226 public typed SDK methods across 18 new sub-clients (agents, annotations, billing, checkpoints, connector_ai, data_apps, data_checks, derivatives, notifications, parameters, pipeline_versions, snippets, support, templates, trash, users, workflows, workspaces) and 12 existing ones; wired all onto `MammothClient`; fixed a Python-3.14-only `except A, B:` (PEP 758) to parenthesized form for 3.12/3.13; regenerated manifests (SDK method count 242→471, all 364 command ops now resolve to a typed symbol); built the manifest-driven Typer runtime (`app.py`, `runtime/invocation.py`, `commands/registry.py`) registering all 435 commands with the global agent-mode options, plus live `version`/`capability`/`schema` discovery handlers; made the docstring gate auto-discover all `mammoth.api` modules | SDK: 1565 unit tests pass; CLI: all 45 contract tests green (runtime tree, capability/schema registries, machine-output/agent-mode/recovery contracts, parity, introspection). Strict mypy + ruff clean on both `mammoth/` (82 files) and `mammoth_cli/` (23 files). Manifest regeneration reproducible (no diff on re-run) | Primary review complete: verified every new sub-client matches the pinned OpenAPI paths/verbs, uses only public `_request_*` seams, carries Google-style docstrings, and adds no CLI private-SDK access; the `workspaces`/`WorkspacesAPI` attribute collision is resolved by exposing the new class as `client.workspace` |
| 2026-07-21 | `923847f` | Phase 3 auth/context/service slice | `context/{credentials,profiles,endpoint,resolver}` (keyring-first credential store with 0600 file fallback, tomlkit profiles, `app-eu` endpoint default, full auth precedence), `services/{protocol,sdk_service,mapping,factory,testing}` (SDK-backed service over the public `MammothClient`, SDK-exception→`CliError` mapping), `commands/{auth,config,context}` bespoke typed callbacks, `runtime/executor` centralizing envelope+error emission | 86 CLI unit tests green; unit tests isolate the OS keyring (in-memory backend) and config dir; strict mypy + ruff clean | Primary review: no second transport and no private SDK members; secrets never logged or echoed |
| 2026-07-21 | `b803cdc` | Phase 3 strict input loading | `runtime/input_loader.load_input_document` resolving `--input`/`--input-format` into a validated request mapping (extension/format inference, stdin-requires-format, stable `EXIT_USAGE` errors, non-mapping rejection); `Invocation.load_input()` exposes it to handlers | 12 new unit tests (98 total) green; mypy + ruff clean | Input text never echoed; embedded secrets cannot leak |
| 2026-07-21 | skill family commit | Phase 8/9 bundled skill + installer (100% command coverage) | `mammoth_cli/bundled_skill/mammoth-cli/` canonical skill (SKILL.md under 500 lines, name+description frontmatter, six one-level references: auth, machine-output, input, safety, jobs-drafts, recovery); `mammoth_cli/skills/installer.py` (copy-not-symlink into codex `.agents/skills`, claude `.claude/skills`, cursor `.cursor/skills` at user/project(git-root) scope; SHA-256 ownership state in `platformdirs.user_data_dir` install-state-v1.json; identical=success, owned=update, unowned/modified=`skill_conflict` unless force→timestamped backup; list/path/uninstall(owned-only)/update); `commands/skill.py` wires the 5 commands; bundled_skill added to pyproject `include` | **435/435 commands implemented (100%)**; 1159 CLI unit tests green; full strict mypy (80 files) + ruff clean | Installer never records credentials; offline package-data lookup; destinations per doc 07 contract |
| 2026-07-21 | Phase 5 view + infra commit | Phase 5 view family (96) + doctor + completion | `view` split into `commands/view.py` (58 sub-client-backed: dataview/checkpoint/data-check/derivative/version/pipeline/task/export/ai) and `commands/view_ops.py` (38 View-object: create/get/delete + draft + 30 transforms). New service seam `MammothService.call_view(view_id, method, **kwargs)` resolves a rich `View` via the public client and invokes transform/draft methods; a `condition` kwarg spec is compiled to the SDK condition object by `services/conditions.compile_condition` (so command modules never import the SDK builder). Also `commands/doctor` (env+connectivity diagnostics) and `commands/completion` (show/install shell completion). Registry now 420 HANDLERS + 3 BESPOKE = 430/435 commands (only the 5 `skill` installer commands remain) | 1149 CLI unit tests green; full strict mypy (78 files) + ruff clean. Live (ws `4`): doctor + completion exit 0; `view list` correctly enforces its required dataset_id (exit 2) | View transforms forward enums as strings and conditions as specs; no SDK types imported in command modules |
| 2026-07-21 | Phase 5-7 wave-2b commit | Phases 5-7: 10 families (support, billing, schedule, agent, ai, addon, external-key, client-app, report, activity) | 101 command handlers across 10 modules (parallel sonnet subagents, reviewed + integrated centrally); registry now 316 handlers (all command_ids valid). support (45, all confirm_target) and billing (23, all confirm_target/yes_always) high-impact guards honored uniformly per the reviewed manifests | 957 CLI unit tests green; full strict mypy (73 files) + ruff clean. Live (ws `4`): report/external-key/agent-session reads exit 0; billing high-impact commands correctly blocked with exit 2 `confirmation_required` when `--yes`/`--confirm` absent; `schedule list` surfaces a server-side API error faithfully (exit 1) | Secrets (external-key secure_key, connector config) are `--input`-only with negative tests |
| 2026-07-21 | Phase 5-7 wave-2a commit | Phases 5-7: 10 families (connector, dashboard, workflow, parameter, data-app, snippet, user, automation, webhook, template) | 118 command handlers across 10 modules (parallel sonnet subagents, reviewed + integrated centrally); registry now 215 handlers (all command_ids valid). Plus a general fix: the SDK service now binds the resolved active project on the `MammothClient` (`set_project_id`), so sub-clients that read project context via `_proj()` (automation, webhook, ...) resolve correctly without an explicit `project_id` kwarg | 635 CLI unit tests green; full strict mypy (63 files) + ruff clean. Live (ws `4`, project `180`): dashboard/workflow/connector/parameter/user/automation/webhook/snippet reads exit 0 with valid envelopes (automation/webhook confirmed after the project-binding fix) | Secrets (connection config/credentials, AI payloads) are `--input`-only, proven by dedicated negative tests |
| 2026-07-21 | Phase 4 wave-1 commit | Phase 4 core resources: 9 families (workspace, dataset, file, job, batch, browse, trash, notification, annotation) | 88 command handlers across 9 `commands/*.py` modules, each drafted by a dedicated subagent from the established folder.py/project.py pattern (generic `service.call` seam, positional/`--input` arg mapping, per-command confirmation guard) and reviewed + integrated centrally; wired in `registry` (97 handlers total, all command_ids valid) | 346 CLI unit tests green (each family asserts exact `call_log` + guard blocking); full-package strict mypy (53 files) + ruff clean. Live (ws `4`, project `180`): `workspace list`, `dataset list`, `browse workspace`, `notification list`, `trash list` all exit 0 with valid envelopes; `batch list` without a project returns exit 2 `project_required`; `browse project` surfaces a server-side 500 faithfully as `api_error`/exit 1 (server issue, not a CLI defect) | Subagent fan-out (9 parallel sonnet agents) validated the pattern scales; main thread owns registry wiring + live verification |
| 2026-07-21 | Phase 4 folder commit | Phase 4 core resources: full `folder` family (9 commands) | `commands/folder` handlers for `list`, `get`, `root`, `create`, `update`, `move`, `trash`, `delete` (prompt_or_yes), `bulk-delete` (prompt_or_yes); all project-scoped (project id from `--project`/active project, folder ids positional or `--input`); wired in `registry` | 16 new unit tests (151 total) asserting project-required, exact `call_log`, and delete-guard blocking; strict mypy + ruff clean. Live (ws `4`, project `180`): `folder list`/`root` exit 0 with valid envelopes; created own folder `875`, `delete` blocked without `--yes` (exit 2), `delete --yes` succeeded, `875` cleaned up; no project-180 folders touched | Second family confirms the handler pattern generalizes cleanly |
| 2026-07-21 | Phase 4 project-mutation commit | Phase 4: mutation confirmation guard + `project` mutating commands | `runtime/confirm.enforce_confirmation` implementing the four reviewed policies (`none`, `prompt_or_yes`, `yes_always`, `confirm_target`) with the `--yes`/`--confirm` global flags added to the generic leaf, `options`, and `Invocation`; prompts only on a real TTY and never in `--no-input`/machine mode; `commands/project` handlers for `create`, `update`, `delete`, `bulk-delete`, `bulk-update` (high-impact `--confirm WORKSPACE`), `sample-flow`, wired in `registry` | 135 CLI unit tests green (12 guard tests + 10 mutation-handler tests asserting guard blocking and exact `call_log`); strict mypy + ruff clean. Live (ws `4`): created throwaway project `1197`, verified `delete` blocked without `--yes` (exit 2 `confirmation_required`), `delete --yes` succeeded (exit 0), project `1197` cleaned up; `update` on the fresh project returned exit 4 `authentication_failed` (server project-scoped RBAC denies update on a just-created project — CLI dispatch/guard/envelope all correct) | Guard is the reusable keystone for all mutating families; no project-180 data touched |
| 2026-07-21 | Phase 4 project-read commit | Phase 4 core resources: read-only `project` family | Generic dispatch seam `services/dispatch.resolve_sdk_method` (resolves a manifest `sdk_symbol` to a bound public sub-client method by class name, refusing private targets) + `MammothService.call(sdk_symbol, **kwargs)` on the SDK service and fake; `runtime/session` (authenticated-service context manager + project-context resolution); `commands/project` handlers for `list`, `get`, `pending-changes`, `resource-status`, `resource-dependencies`, `publish-credentials`, wired in `registry` | 113 CLI unit tests green (dispatch, input, project handlers with a call-recording fake); strict mypy + ruff clean. Live (ws `4`, project `180`): `project list` (8 projects, `180` present), `get 180`, `pending-changes 180`, `resource-status 180` all exit 0 with valid envelopes; `get 999999999` returns a stderr error envelope, exit 1 | Read-only only; no project-180 data mutated. Note: not-found currently maps to generic `api_error`/exit 1 — refine `mapping` to `resource_not_found`/exit 5 when building the mutation slice |

### Phase 1 evidence and decisions

- Pinned OpenAPI SHA-256 `0c7c777f36cd81f48fe676c04f5cb06c74163081c0870c775a57da8dff4a5f04`
  (234 paths, 376 operations, 770 schemas). This differs from the plan's earlier
  `6b2c8647...` digest because the live generator is nondeterministic (examples,
  a project-color default, parameter order, one description change). Path and
  operation counts are stable at 234/376. Per the plan's snapshot-refresh process
  the primary reviewed and pinned the exact fetched bytes; the difference is
  examples/description noise, not a semantic contract change.
- Primary dev interpreter is Python 3.14.3 (venv). Plan named 3.14.3; 3.14.4 is
  also available. jsonschema and types-PyYAML added to CLI dev deps.
- 11 protocol_only operations: health, unsubscribe, Stripe webhook, 3 Shopify
  GDPR hooks, provider deauthorization, OAuth callback, mm-ue telemetry, and 2
  published-dashboard viewer telemetry endpoints. Full list in the parity report.
- 0 deprecated and 0 server_unavailable operations (no server evidence; a
  permission error is never `server_unavailable`).
- 4 reviewed SDK-only exemptions (no CLI command): `DatasetsAPI.bulk_delete`
  (forbidden targetless bulk delete), `PipelineAPI.draft_mode` (typed draft seam
  behind the draft verbs), `MammothClient.find_dataset_for_dataview` (private
  resolver), `View.draft` (SDK-only compound context manager).

## Open TODOs

- [x] Commit this plan set (`bb2557f`).
- [x] Create and review the OpenAPI disposition inventory (`spec/manifests/openapi-operations.yaml`).
- [x] Create and review the SDK method inventory (`spec/manifests/sdk-methods.yaml`).
- [x] Create exact command specifications (`spec/manifests/commands/*.yaml`, 435 records).
- [x] Create red-first tests (`mammoth-cli/tests/contract/`, expected red baseline saved).
- [x] Add public typed API groups for all missing command operations (Phase 2):
  226 methods across 30 sub-clients; all 364 command operations now resolve to a
  typed public SDK symbol.
- [~] Resolve the mandatory SDK defect list (Phase 2): public `close()`/context
  manager (done), dataview->dataset resolver (done), server-backed draft state
  (done), typed pagination `Page` (done). Still open: typed job start/wait
  results, typed request/result models, typed export destination models, secret
  metadata, atomic downloads, project lookup >100, and the reproducible Pydantic
  v2 wire-model codegen.
- [x] Build the CLI runtime core (Phase 3): manifest-driven Typer registration of
  all 435 commands, global agent-mode options on every command, typed
  `Invocation`, handler registry, stable success/error envelopes, and live
  `version`/`capability`/`schema` discovery handlers.
- [ ] Implement remaining Phase 3 runtime seams (service protocol + SDK adapter,
  profile/endpoint/auth resolution, keyring/file storage, project context,
  strict input loading) and the per-family command handlers (Phases 4-7).
- [ ] Documentation, skill, installers, and final gates (Phases 8-10).
- [ ] Keep this ledger current.

## Final audit template

Complete this section before handoff:

```text
OpenAPI snapshot SHA-256:
OpenAPI operation count:
OpenAPI records by disposition:
Reviewed command dispositions:
Reviewed alias dispositions:
Reviewed protocol-only dispositions:
Reviewed server-unavailable dispositions:
Public SDK method count:
SDK methods with command or alias:
Canonical CLI command count:
Commands with unit evidence:
Commands with subprocess evidence:
Commands with guarded live evidence:
Commands with approved live exemptions:
SDK additions:
SDK repairs:
Transforms with output-data evidence:
Transforms with draft evidence:
Transforms with rollback evidence:
Unresolved manifest fields:
Manifest/schema validation result:
Unit/contract test result:
Live test result:
Leak audit result:
Secret audit result:
STE result:
Skill validation result:
Installer result by platform:
Known server-unavailable operations:
Remaining TODOs:
Final reviewer:
```
