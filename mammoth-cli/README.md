# mammoth-cli

Drive the [Mammoth Analytics](https://mammoth.io) platform from your terminal.
The `mammoth` command uploads data, runs pipeline transformations, manages
projects and dashboards, and exports results — for people at a shell and for
autonomous agents alike.

[![PyPI](https://img.shields.io/pypi/v/mammoth-cli)](https://pypi.org/project/mammoth-cli/)
[![Python](https://img.shields.io/pypi/pyversions/mammoth-cli)](https://pypi.org/project/mammoth-cli/)
[![License](https://img.shields.io/pypi/l/mammoth-cli)](https://github.com/EdgeMetric/mammothsdk/blob/main/mammoth-cli/LICENSE)

- **Human-friendly by default.** In a terminal, commands print a readable table.
- **Agent-native.** When output is piped, you get a stable JSON envelope with a
  documented schema, exit codes, and error codes — no flags required.
- **Safe.** Every mutation carries a reviewed confirmation policy, so a
  destructive command never runs unattended by accident.
- **Discoverable.** `mammoth capability list` and `mammoth schema get` describe
  every command, so an agent can learn the surface at runtime.

The CLI is built on the public [`mammoth-io`](https://pypi.org/project/mammoth-io/)
SDK. It adds no second HTTP client and calls no private SDK members.

## Install

```bash
uv tool install mammoth-cli      # recommended: isolated, on your PATH
# or
pipx install mammoth-cli
# or
python -m pip install mammoth-cli
```

Then confirm the install:

```bash
mammoth --version
```

The CLI supports Python 3.12, 3.13, and 3.14. For the one-line installers and
the verified (signed) install flow, see [docs/installation.md](docs/installation.md).

## Quick start

```bash
mammoth auth login -w 4          # log in once; the secret goes to your OS keyring
mammoth doctor                   # confirm credentials resolve and the API answers
mammoth project list             # a table in a terminal, JSON when piped
mammoth dataset list --project 180
```

Full walkthrough: [docs/quickstart.md](docs/quickstart.md).

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
  --input '{"expression": "price * qty", "new_column": "total"}'
```

Install the bundled agent skill for Claude Code, Codex, and Cursor:

```bash
mammoth skill install
```

See [docs/agents.md](docs/agents.md) and the
[agent skill](mammoth_cli/bundled_skill/mammoth-cli/SKILL.md).

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

Agent-readable indexes: [`docs/llms.txt`](docs/llms.txt) and
[`docs/llms-full.txt`](docs/llms-full.txt).

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
