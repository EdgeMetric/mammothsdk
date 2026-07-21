# Autonomous implementation runbook

## Ownership

The primary agent owns:

- `add-cli-for-mammoth`.
- This plan set.
- OpenAPI and SDK inventory review.
- Shared interfaces.
- Integration and final acceptance.

Worker agents do not edit the plan or target branch. Each worker uses an
isolated worktree and one focused branch.

Use this exact worktree protocol:

```text
Integration branch: add-cli-for-mammoth
Worker branch: cli/<phase>/<packet-id>
Worktree: ../mm-pysdk-worktrees/<packet-id>
Maximum active workers: 3
```

The task packet records the current integration `base_sha`. Before work, the
worker verifies that SHA and its merge base. It owns only listed paths and
manifest IDs. The primary reviews the returned commit, verifies its merge base,
and cherry-picks it in dependency order. The primary resolves no worker merge
conflict: reject the packet and have the worker rebase onto the newly recorded
SHA. Remove only the explicit recorded worktree after handoff.

## Worker task packet

Every task must include:

- Exact OpenAPI operation IDs.
- Exact SDK symbols or required SDK additions.
- Exact command-spec records.
- Files the worker owns.
- Tests that must be red first.
- Commands required for verification.
- Safety and secret classifications.
- Documentation and STE requirements.
- A prohibition on unrelated changes.

Required worker report:

```text
Task:
Base SHA:
Red baseline commit:
Green commit:
Files changed:
OpenAPI operations completed:
SDK symbols completed:
Commands completed:
Tests added:
Commands run:
Results:
Known limitations:
Security notes:
Documentation notes:
```

## Primary review protocol

For every worker commit:

1. Read the complete diff.
2. Match it to assigned operation and command records.
3. Confirm that tests existed and failed before the implementation.
4. Run targeted tests.
5. Run strict typing and lint checks.
6. Check public SDK-only access.
7. Check secret transport and redaction.
8. Check mutation safety and waiting.
9. Check STE user-facing text.
10. Reject unrelated or untyped changes.
11. Cherry-pick only after all checks pass.
12. Update the checklist, audit, notes, and TODO ledger.

## Phase 0: Commit the specification

- [x] Review all plan documents.
- [x] Select Python 3.14.3 for primary development commands.
- [x] Confirm clean branch state.
- [x] Commit this plan set before feature code.
- [x] Record the commit in the audit ledger.

## Phase 1: Inventory and red tests

- [ ] Add the OpenAPI sync script.
- [ ] Pin the inspected OpenAPI snapshot and digest.
- [ ] Generate all 376 OpenAPI records.
- [ ] Generate all 242 SDK records.
- [ ] Create disposition records for every OpenAPI operation.
- [ ] Review every `protocol_only` and unavailable disposition.
- [ ] Create exact command-spec records.
- [ ] Add parity and manifest schemas.
- [ ] Add all red-first tests from the TDD document.
- [ ] Save the expected red test report.
- [ ] Block command work until primary review approves this gate.

Do not use live credentials during this phase. The OpenAPI document is public,
and all inventory generation must work without a Mammoth login.

## Phase 2: SDK foundation

- [ ] Generate Pydantic v2 wire models from the snapshot.
- [ ] Add reproducible generation checks.
- [ ] Add public typed API groups for missing command operations.
- [ ] Add public dataview/dataset resolution.
- [ ] Add typed pagination pages.
- [ ] Add typed job start/wait results.
- [ ] Add typed secret metadata.
- [ ] Add and test public SDK session close/context-manager behavior.
- [ ] Add typed task and pipeline unions.
- [ ] Add server-backed draft state.
- [ ] Add typed export destination and common-option models.
- [ ] Fix atomic download behavior.
- [ ] Resolve all mandatory SDK audit defects.
- [ ] Run SDK unit and safe live tests.

Use `mammoth/openapi/codegen.toml` and
`mammoth/scripts/generate_openapi_models.py`. The wrapper invokes the locked
datamodel-code-generator with the pinned snapshot, OpenAPI input, Pydantic v2
base models, Python 3.12 syntax, standard collections, and union operators. It
writes committed internal wire types to
`mammoth/_generated/openapi_models.py`, formats them, and emits a model-name map
for collisions. Generated classes are internal wire types; curated public SDK
request and result models wrap them. Preserve OpenAPI `oneOf`, nullable fields,
discriminators, and `additionalProperties`; do not weaken a closed schema. A
second generation must produce no diff. Generate only schemas reachable from
reviewed command operations and shared error/job envelopes.

## Phase 3: CLI runtime

- [ ] Scaffold `mammoth-cli` and its lockfile.
- [ ] Add `mammoth` and module entry points.
- [ ] Implement the service protocol and SDK adapter.
- [ ] Implement profile and endpoint resolution.
- [ ] Implement keyring and explicit file storage.
- [ ] Implement project context.
- [ ] Implement input loading and precedence.
- [ ] Implement result normalization.
- [ ] Implement output renderers.
- [ ] Implement errors and exit statuses.
- [ ] Implement prompt, color, progress, and interruption policy.
- [ ] Implement completion infrastructure.
- [ ] Make the shared runtime tests green.

## Phase 4: Core resources

- [ ] Authentication, configuration, context, and doctor.
- [ ] Workspace and project operations.
- [ ] Folder, dataset, dataview, view, trash, and restore operations.
- [ ] File, job, batch, and browse operations.
- [ ] Notifications and annotations.
- [ ] Review and integrate each family separately.

## Phase 5: Pipelines and data operations

- [ ] Pipeline, task, rerun, and preview.
- [ ] Draft mode across separate processes.
- [ ] Checkpoints and versions.
- [ ] Data checks and derivatives.
- [ ] Conditional formats.
- [ ] Every typed transformation.
- [ ] Output-data, draft, and rollback live evidence.

## Phase 6: Integrations and exports

- [ ] Connectors and connections.
- [ ] Connector dataset configurations and AI chat.
- [ ] Webhooks.
- [ ] All pipeline export CRUD operations.
- [ ] Every typed export destination.
- [ ] Publish credentials and publish-to-DB.
- [ ] External contract fixtures and guarded live tests.

## Phase 7: Workflows and administration

- [ ] Workflows, blocks, graph, canvas, and templates.
- [ ] Automations and schedules.
- [ ] Parameters and snippets.
- [ ] Dashboards and data apps.
- [ ] Agent chat and sessions.
- [ ] Client apps and external keys.
- [ ] User profile, preferences, and avatar.
- [ ] Reports and activity logs.
- [ ] Support and billing commands.
- [ ] Confirm all high-impact guards.

## Phase 8: Documentation and agent skill

Follow the exact package and destination contract in
`07-packaging-install-skill.md`.

- [ ] Add the Mammoth STE terminology and Vale rules.
- [ ] Write installation and five-minute quick start.
- [ ] Write authentication, profiles, prefixes, and project context.
- [ ] Generate complete command reference and schemas.
- [ ] Write agent/CI, safety, troubleshooting, upgrade, and uninstall guides.
- [ ] Initialize the `mammoth-cli` skill with the skill-creator tooling.
- [ ] Use the exact skill folder name `mammoth-cli`.
- [ ] Add only `SKILL.md`, `agents/openai.yaml`, and required one-level
  `references/` or deterministic `scripts/` resources. Do not add a skill-local
  README, installation guide, changelog, or duplicated command reference.
- [ ] Keep `SKILL.md` concise, imperative, and under 500 lines. Put all trigger
  conditions in its frontmatter description. Keep only `name` and `description`
  in the frontmatter.
- [ ] Generate `agents/openai.yaml` from the completed skill with the
  skill-creator generator. Do not hand-maintain divergent metadata.
- [ ] Put detailed command schemas in one-level references. State exactly when
  an agent must read each reference. Add a contents list to references longer
  than 100 lines.
- [ ] Add thin install adapters for the native Codex, Claude Code, and Cursor
  discovery locations. Keep one canonical skill source in the package.
- [ ] Implement skill install, list, path, update, and uninstall.
- [ ] Run `quick_validate.py` and test every bundled deterministic script.
- [ ] Forward-test with fresh low-context agents. Give each agent the raw skill
  and a realistic task, not the expected answer or known defect.

Skill commands:

```text
mammoth skill install --agent codex|claude|cursor|all --scope user|project
mammoth skill list
mammoth skill path
mammoth skill update
mammoth skill uninstall
```

## Phase 9: Installation and release preparation

Follow the exact artifact, installer, platform, ownership, rollback, and test
contract in `07-packaging-install-skill.md`.

- [ ] Support `uv tool install mammoth-cli`.
- [ ] Support `pipx install mammoth-cli`.
- [ ] Support `pip install mammoth-cli`.
- [ ] Add POSIX and PowerShell installers.
- [ ] Add checksums and attestations.
- [ ] Add upgrade and uninstall ownership records.
- [ ] Test all supported systems.

Stable installer targets:

```bash
curl -fsSL https://github.com/EdgeMetric/mm-pysdk/releases/latest/download/mammoth-install.sh | sh
```

```powershell
irm https://github.com/EdgeMetric/mm-pysdk/releases/latest/download/mammoth-install.ps1 | iex
```

The one-line forms are convenience paths. The recommended verified flow and
all option syntax are defined in `07-packaging-install-skill.md`.

## Phase 10: Final gates

- [ ] All parity and command manifests are complete.
- [ ] All unit and contract tests pass.
- [ ] Strict mypy, Ruff, and formatting checks pass.
- [ ] Generated artifacts have no diff.
- [ ] Package and installer tests pass.
- [ ] Documentation and CLI text pass STE checks.
- [ ] Skill validation and forward tests pass.
- [ ] Dedicated-tenant live tests pass.
- [ ] The leak audit passes.
- [ ] The complete branch diff receives primary review.
- [ ] Audit, notes, blockers, and TODOs are current.
- [ ] Final report lists operations, evidence, and any server-unavailable records.

For live verification, create a new isolated project in workspace `4` on the
`release` server. Never mutate an existing project during recon or test runs.
