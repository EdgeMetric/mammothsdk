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
- Therefore the supplied credentials are verified for authentication and
  project create/list/delete, but not for dataset creation, file upload, view
  operations, or transformations. Do not claim that live bulk replace or the
  full acceptance suite passed.
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

## Blockers before live acceptance

- [x] Store the supplied test credentials in the ignored local `.env.plan`.
- [x] Record the allowlisted test workspace ID as `4`.
- [x] Record the test server prefix as `release`.
- [x] Verify that the credentials can create and delete an isolated project.
- [ ] Grant the test principal file-upload and dataset-creation access in
  workspace `4`, or provide a disposable workspace with those permissions.
- [ ] Re-run isolated dataset, view, query, pipeline, and bulk-replace recon
  after the permission blocker is removed.
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
- [ ] Resolve the mandatory SDK defect list (Phase 2): public `close()`/context
  manager, dataview->dataset resolver, server-backed draft state, typed
  pagination, typed job start/wait, typed request/result models, typed export
  destinations, secret metadata, atomic downloads, project lookup >100.
- [ ] Implement the CLI runtime and command handlers (Phases 3-7).
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
