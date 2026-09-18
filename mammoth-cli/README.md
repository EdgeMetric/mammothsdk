# mammoth-cli

Use [Mammoth Analytics](https://mammoth.io) from a terminal. The `mammoth`
command covers data import and export, transformations, project organization,
automation, and administration. Its interface is designed to be readable at a
shell and predictable in scripts and agent runs.

[![PyPI](https://img.shields.io/pypi/v/mammoth-cli)](https://pypi.org/project/mammoth-cli/)
[![Python](https://img.shields.io/pypi/pyversions/mammoth-cli)](https://pypi.org/project/mammoth-cli/)
[![License](https://img.shields.io/pypi/l/mammoth-cli)](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/LICENSE)

- **Human-friendly by default.** In a terminal, commands print a readable table.
- **Agent-native.** When output is piped, you get a stable JSON envelope with a
  documented schema, exit codes, and error codes — no flags required.
- **Guarded mutations.** Commands expose their confirmation policy; promptless
  destructive operations require an explicit `--yes`.
- **Discoverable.** `mammoth capability list` and `mammoth schema get` describe
  every command, so an agent can learn the surface at runtime.

The CLI is built on the public [`mammoth-io`](https://pypi.org/project/mammoth-io/)
SDK. It adds no second HTTP client and calls no private SDK members.

See the [capability matrix](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/release-capability-matrix.md)
for current row-level coverage and evidence status.

## Install

Install the CLI without a preinstalled Python tool manager:

```bash
curl -fsSL https://raw.githubusercontent.com/EdgeMetric/mammothsdk/main/mammoth-cli/installers/mammoth-install.sh | bash
```

Open a new shell if needed so the installer-added tool directory is on PATH,
then confirm it works:

```bash
mammoth --version
```

The installer bootstraps its own `uv` tool environment when needed and installs
the bundled agent skill. For an exact, reproducible release use `--version
X.Y.Z`; the installer has no normal prompts. See
[Installation](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/installation.md) for that option and the SDK-only pip
installation path.

## First run: authenticate, check, then discover

Authentication is the first operational step. In an evaluated or isolated run
with a controller-provided credential broker/sidecar, use that broker's
readiness check; do not inspect saved profiles, run login, or run doctor, and
stop if the broker is absent. In an ordinary shell, check the selected profile;
this is a local presence check, not a live access test. If the profile or
stored credentials are absent, log in before running `doctor` or any data command:

```bash
mammoth skill list --output json --no-input
mammoth skill path --output json --no-input
# Read the installed SKILL.md before operating.
mammoth auth status --output json --no-input
# Compare the reported endpoint with the intended target before doctor.
# Use app for production; use release only when explicitly intended.
# Human terminal only, if profile or stored credentials are absent:
mammoth auth login
# Then verify configuration, credentials, endpoint, and connectivity:
mammoth doctor --output json --no-input
# Then discover a task-specific route:
mammoth schema find "TASK OR RESOURCE" --output json --no-input
mammoth schema get COMMAND_ID --output json --no-input
# Optional API-binding inventory (not the complete CLI surface):
mammoth capability list --output json --no-input
```

For an agent or CI, do not request or paste secrets into chat, prompts, shell
history, or command arguments. On POSIX, put the required JSON credentials in a
private owner-only (0600) file outside the repository and pass its path to:

```bash
mammoth auth login --input /private/path/credentials.json --storage file \
  --output json --no-input
```

On Windows, use the approved OS keyring or credential broker instead; do not
use a file fallback unless its ACL hardening is approved, and stop if neither
is available.

The default server prefix is `app`; pass `--server-prefix release` only when
the release endpoint is explicitly intended. Compare the endpoint reported by
`auth status` with the intended target before running `doctor`; if it does not
match, stop and switch to a separate correctly configured profile. See
[Authentication](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/authentication.md)
for the required JSON fields and profile behavior. After `doctor` succeeds,
resolve the exact workspace, project, dataset, and view from read results
before operating; verify every mutation. Use `schema find`/`schema get` for
typed and local CLI routes; `capability list` is only an API-binding inventory
and may omit them. Full walkthrough:
[docs/quickstart.md](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/quickstart.md).

## Built for agents and CI

Piping or redirecting output yields the machine envelope, and `--no-input` turns
on automatically off a terminal, so an agent needs no special flags:

```bash
mammoth project list | jq '.data'
```

To be explicit, pass `--output json --no-input`. Log in without a prompt with
the private, permission-checked file described above:

```bash
mammoth auth login --input /private/path/credentials.json --storage file \
  --output json --no-input
```

Feed multi-field requests as one document instead of many flags:

```bash
mammoth view transform math 1039 --project 180 \
  --input '{"expression": "Unit Price * Quantity", "new_column": "Revenue"}'
```

For pipeline transformations, prefer the typed commands and inspect their
schemas before composing input. For example:

```bash
mammoth schema get view.transform.filter --output json --no-input
mammoth schema get view.transform.math --output json --no-input
mammoth schema get view.transform.substring --output json --no-input
```

The generic `view task add`, `view task preview`, and `view task update`
commands are low-level expert routes. Their `task_spec` object is intentionally
opaque in the installed schema; use a typed `view transform` command instead
of inventing task fields. High-impact imports must also identify and confirm
their target explicitly, for example:

```bash
mammoth dashboard import-workbook ./sample.twbx --project 456 \
  --yes --confirm 456 --output json --no-input
```

The sample path and project ID are placeholders for a local workbook and a
project you have resolved and are authorized to modify.

The one-line installer already set up the bundled agent skill for Claude Code,
Codex, and Cursor. To repair or refresh the installed copy:

```bash
mammoth skill install
```

Start with [Agent handover and operation](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/agents.md), then load the
[bundled agent skill](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/mammoth_cli/bundled_skill/mammoth-cli/SKILL.md) from the
installed CLI. The skill routes a task to only the relevant recipe or command
catalog section; it does not require an agent to absorb the whole reference.

For a fresh external shell agent, start with the shipped
[portable task-start playbook](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/mammoth_cli/bundled_skill/mammoth-cli/references/task-start.md).

For an unattended task, use the handover loop: discover its schema, resolve
every resource in explicit scope, operate from IDs returned by reads, verify
the requested outcome, then record a nonsecret checkpoint. Examples in this
repository are nonexhaustive. The CLI never requires backend column identifiers:
inputs name columns by their display names. Do not infer a usable default view
from a dataset; run `view list DATASET_ID` and choose a view explicitly.

If another agent must continue the work, write the nonsecret checkpoint format
described in [Portable agent handoff](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/agent-handoff.md). It records scope,
intent, verified evidence, jobs/unknown outcomes, and cleanup ownership without
putting credentials into the handoff.

## Give your coding agent the CLI playbook

The bundled skill describes authentication, discovery, structured input, job
handling, and confirmations. Install it for the supported coding-agent tools:

```bash
mammoth skill install
mammoth skill list
```

The default target is user scope. To inspect destinations before writing, run
`mammoth skill path`. To install only for one agent in the current project, use
structured input:

```bash
mammoth skill install --input '{"agents": ["codex"], "scope": "project"}'
```

Use `mammoth skill update` after a CLI upgrade. It refreshes copies owned by the
installer and reports modified copies instead of silently replacing them.

## What you can do

| Area | Command families |
|---|---|
| Data in and out | `file`, `dataset`, `connector`, `addon` |
| Shape and analyze | `view`, `dataset`, `ai` |
| Organize | `project`, `folder`, `dashboard`, `report`, `template` |
| Automate | `automation`, `workflow`, `schedule`, `batch`, `webhook` |
| Administer | `workspace`, `user`, `billing`, `client-app`, `external-key` |
| Operate the CLI | `auth`, `context`, `config`, `doctor`, `capability`, `schema`, `skill`, `upgrade` |

The full generated list is in [docs/reference/commands.md](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/reference/commands.md).

## Documentation

| Guide | What it covers |
|---|---|
| [Installation](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/installation.md) | Install the CLI and the agent skill. |
| [Quick start](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/quickstart.md) | Log in and run your first commands. |
| [Authentication](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/authentication.md) | Getting an API key, login, profiles, projects. |
| [Agent handover and operation](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/agents.md) | Cold start, discovery, checkpoints, recovery. |
| [Portable handoff format](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/agent-handoff.md) | Nonsecret checkpoint schema and receiving procedure. |
| [Bundled agent skill](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/mammoth_cli/bundled_skill/mammoth-cli/SKILL.md) | Focused routing for shell-capable agents. |
| [Safe mutation](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/safety.md) | Mutation classes and confirmation policies. |
| [Output and errors](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/reference/output-and-errors.md) | Envelopes, exit codes, error codes. |
| [Global flags](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/reference/global-flags.md) | The flags every command shares. |
| [Troubleshooting](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/troubleshooting.md) | Exit codes, error envelopes, recovery. |
| [Upgrade](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/upgrade.md) / [Uninstall](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/uninstall.md) | Keep the CLI current, or remove it. |
| [Command reference](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/reference/commands.md) | Every command, grouped by family. |

Start with **Quick start** for a copy-paste workflow, **Authentication** for
profiles and non-interactive login, or **Agent handover and operation** for a
fresh-agent task. The command reference is generated; use `mammoth schema get
COMMAND.ID` to verify a request shape against the installed CLI.

Agent-readable indexes: [`docs/llms.txt`](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/llms.txt) and
[`docs/llms-full.txt`](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/llms-full.txt).

## Capability-matrix status

The committed machine-readable release matrix is the canonical repository
inventory; historical readiness records are kept separately from this summary. The
repository-facing summary is
[`docs/agent-capability-coverage.md`](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/agent-capability-coverage.md).
The current release snapshot contains **528 operations across 355 paths** (the
historical pinned M0 snapshot was **445 operations across 287 paths**).
The matrix separates **Core** ETL/workflow capabilities from **Miscellaneous**
surfaces. Its live status counts are intentionally not duplicated here; read
the linked row-level matrix for the current values. It does not declare Full
readiness: matrix rows are planning/review status, not release qualification
or live semantic proof.
No status changes are inferred from an OpenAPI refresh: additions begin
Unassessed and removals or operation-ID changes require review. Use
`scripts/report_release_capability_drift.py --help` to produce a deterministic
local review queue from a candidate OpenAPI JSON; it never implements routes or
promotes support. See the [capability drift workflow](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/capability-drift-workflow.md)
for the required row fields and review steps. No secrets or live evidence are
copied into this README.
The sanitized [row-level release matrix](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/release-capability-matrix.md)
and [machine-readable matrix](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/release-capability-matrix.json) preserve all
528 method/path line items without pilot payloads or credentials.

### Core top-15 snapshot

This compact table is a navigation summary, not a family-wide qualification
claim. The linked matrix row is canonical; `Unassessed` means no support claim.

| Area | Capability | ID | Status | Evidence/limitation |
|---|---|---:|---|---|
| Project | List projects | REL-174 | Partial | One bounded project-list read. |
| Project | Create project | REL-431 | Unassessed | No owned project lifecycle evidence. |
| Project | Update project | REL-286 | Unassessed | No approved lifecycle evidence. |
| Project | Delete project | REL-037 | Unassessed | Protected project scope; no disposable project. |
| Dataset | Create dataset | REL-443 | Partial | Owned disposable create/readback/cleanup evidence. |
| Dataset | List datasets | REL-191 | Partial | Bounded list/readback evidence. |
| Dataset | Get dataset | REL-192 | Partial | One retained-resource read. |
| Dataset | Delete dataset | REL-044 | Partial | Owned delete and absence readback; variants remain untested. |
| View | Create/duplicate view | REL-446 | Partial | One disposable view lifecycle. |
| View | List views | REL-197 | Partial | One retained view/parent scope. |
| View | Get view | REL-198 | Partial | Positive and invalid-parent controls. |
| View | Pipeline task readback | REL-214 | Partial | Typed transforms require schema discovery; bounded task-list evidence. |
| Dashboard | Create dashboard | REL-326 | Unassessed | No current approved create fixture. |
| Dashboard | Get dashboard | REL-107 | Partial | One retained dashboard read. |
| Folder | Get folder | REL-224 | Full | Public CLI 1.1.12 receipt covers fields, filtered list, errors, lifecycle, and final absence; folder family remains incomplete. |

Use the [canonical matrix](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/release-capability-matrix.md) for the full
528-row inventory and exact evidence links.

## Compatibility

`mammoth-cli` follows [Semantic Versioning](https://semver.org) for the 2.x
series:

- The machine-output and error-envelope contract is stable. `SCHEMA_VERSION`
  (see `mammoth_cli/__init__.py`) identifies it and never changes incompatibly
  within a major version. New fields may be added; existing ones are preserved.
- The CLI surface is stable. Command names, flags, and exit codes are not
  removed or repurposed within a major version.
- Bug fixes ship in patch releases. Additive changes ship in minor releases.

## Development

```bash
pytest tests/ -q                 # unit + contract tests (live tests deselected)
ruff check mammoth_cli scripts tests
mypy mammoth_cli
make cli-docs-check              # documentation gates
```

Build scripts under `scripts/` regenerate the manifests and the documentation
corpus offline. Release and packaging details live in
[RELEASING.md](https://github.com/EdgeMetric/mammothsdk/blob/main/RELEASING.md).

## License

See [LICENSE](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/LICENSE). Source: https://github.com/EdgeMetric/mammothsdk
