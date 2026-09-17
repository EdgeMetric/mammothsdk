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

Agent-oriented interfaces are not a claim that autonomous long pipelines or
every release API operation are qualified. See the
[capability matrix](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/docs/release-capability-matrix.md)
for current coverage.

## Install

One step, no prerequisites. This installs `uv` if you do not already have it,
the `mammoth` CLI, and the agent skill for Claude Code, Codex, and Cursor:

```bash
curl -fsSL https://github.com/EdgeMetric/mammothsdk/releases/latest/download/mammoth-install.sh | sh
```

Windows PowerShell:

```powershell
irm https://github.com/EdgeMetric/mammothsdk/releases/latest/download/mammoth-install.ps1 | iex
```

Then confirm it works:

```bash
mammoth --version
mammoth doctor          # checks config, credentials, endpoint, connectivity
```

<details>
<summary>Already have a Python tool manager?</summary>

```bash
uv tool install mammoth-cli      # isolated, on your PATH
pipx install mammoth-cli
python -m pip install mammoth-cli
```

</details>

The CLI supports Python 3.12, 3.13, and 3.14. These one-line commands execute
downloaded code; for checksum verification, see
[docs/installation.md](docs/installation.md). A Sigstore signature is an
additional verification step only when that release actually includes its
`SHA256SUMS.sigstore.json` bundle.

## Quick start

```bash
mammoth auth login               # prompts for API key, API secret, workspace id
mammoth doctor                   # confirm credentials resolve and the API answers
mammoth project list             # a table in a terminal, JSON when piped
mammoth dataset list --project 180
```

Full walkthrough: [docs/quickstart.md](docs/quickstart.md).

The login command has no workspace shortcut flag. For CI or an agent, use a
protected request document instead:

```bash
chmod 600 creds.json
mammoth auth login --input creds.json --output json --no-input
```

## Built for agents and CI

Piping or redirecting output yields the machine envelope, and `--no-input` turns
on automatically off a terminal, so an agent needs no special flags:

```bash
mammoth project list | jq '.data'
```

To be explicit, pass `--output json --no-input`. Log in without a prompt with a
permission-checked file:

```bash
mammoth auth login --input creds.json --output json --no-input
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
Codex, and Cursor. If you installed with `uv`, `pipx`, or `pip` instead:

```bash
mammoth skill install
```

See [docs/agents.md](docs/agents.md) and the
[agent skill](mammoth_cli/bundled_skill/mammoth-cli/SKILL.md).

For a fresh external shell agent, start with the shipped
[portable task-start playbook](mammoth_cli/bundled_skill/mammoth-cli/references/task-start.md).

For an unattended task, use the open-ended loop documented in
[Agent and CI usage](docs/agents.md): discover a capability and its schema,
resolve every resource in its explicit scope, compose operations from the IDs
returned by reads, verify the requested outcome, then recover or clean up from
the observed state. Examples in this repository are nonexhaustive. The CLI
never requires an agent to use backend column identifiers: inputs name columns
by their display names. Do not infer a usable default view from a dataset; run
`view list DATASET_ID` and choose a view explicitly.

If another agent must continue the work, write the nonsecret checkpoint format
described in [Portable agent handoff](docs/agent-handoff.md). It records scope,
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

The full generated list is in [docs/reference/commands.md](docs/reference/commands.md).

## Documentation

| Guide | What it covers |
|---|---|
| [Installation](docs/installation.md) | Install the CLI and the agent skill. |
| [Quick start](docs/quickstart.md) | Log in and run your first commands. |
| [Authentication](docs/authentication.md) | Getting an API key, login, profiles, projects. |
| [Agent and CI usage](docs/agents.md) | Machine output, structured input, patterns. |
| [Safe mutation](docs/safety.md) | Mutation classes and confirmation policies. |
| [Output and errors](docs/reference/output-and-errors.md) | Envelopes, exit codes, error codes. |
| [Global flags](docs/reference/global-flags.md) | The flags every command shares. |
| [Troubleshooting](docs/troubleshooting.md) | Exit codes, error envelopes, recovery. |
| [Upgrade](docs/upgrade.md) / [Uninstall](docs/uninstall.md) | Keep the CLI current, or remove it. |
| [Command reference](docs/reference/commands.md) | Every command, grouped by family. |

Start with **Quick start** for a copy-paste workflow, **Authentication** for
profiles and non-interactive login, or **Agent and CI usage** for schema-driven
automation. The command reference is generated; use `mammoth schema get
COMMAND.ID` to verify a request shape against the installed CLI.

Agent-readable indexes: [`docs/llms.txt`](docs/llms.txt) and
[`docs/llms-full.txt`](docs/llms-full.txt).

## Capability-matrix status

The reviewed OpenAPI capability matrix is maintained in the readiness
workbook; the repository-facing summary is
[`docs/agent-capability-coverage.md`](docs/agent-capability-coverage.md).
The current release snapshot contains **528 operations across 355 paths** (the
historical pinned M0 snapshot was **445 operations across 287 paths**).
The matrix separates **Core** ETL/workflow capabilities from **Miscellaneous**
surfaces and currently records **7 Partial** and **521 Unassessed** rows. It
does not declare any unsupported **Full** readiness claim: these counts are
planning/review status, not release qualification or live semantic proof.
The workbook remains authoritative for row-level ownership, evidence, and
qualification gates; no secrets or live evidence are copied into this README.
The sanitized [row-level release matrix](docs/release-capability-matrix.md)
and [machine-readable matrix](docs/release-capability-matrix.json) preserve all
528 method/path line items without pilot payloads or credentials.

## Compatibility

`mammoth-cli` follows [Semantic Versioning](https://semver.org) for the 1.x
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
[../RELEASING.md](../RELEASING.md).

## License

See [LICENSE](LICENSE). Source: https://github.com/EdgeMetric/mammothsdk
