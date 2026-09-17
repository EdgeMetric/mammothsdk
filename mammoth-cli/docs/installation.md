# Installation

[Documentation index](llms.txt)

Install `mammoth-cli` as an isolated command-line tool, then confirm that the
`mammoth` executable is on your PATH. The supported user-facing CLI path is the
pinned installer for hosts without a preinstalled Python tool manager; it
bootstraps `uv` when `uv` is absent and requires curl/bash/network access.

## Pinned CLI installer

Run:

```bash
curl -fsSL https://raw.githubusercontent.com/EdgeMetric/mammothsdk/main/mammoth-cli/installers/mammoth-install.sh | bash -s -- --version 1.1.12 --noninteractive
```

Confirm the result:

```bash
mammoth --version
```

If `mammoth` is not found after installation, open a new shell so the
installer's tool bin directory is on your PATH.

## SDK installation

The Python SDK remains independently installable with pip:

```bash
python -m pip install mammoth-io==0.7.1
```

This SDK command does not install the CLI.

## Install the agent skill

```bash
mammoth skill install --output json --no-input          # all agents, user scope
mammoth skill path --output json --no-input             # show source + targets
mammoth skill list --output json --no-input
```

The skill installs for Codex, Claude Code, and Cursor. Pass an `--input`
document with `{"agents": ["claude"], "scope": "project"}` to narrow the target.

Use `mammoth skill path` before a project-scoped install to review its target.
`mammoth skill list` reports whether installed copies are intact; `mammoth skill
update` refreshes copies that the installer owns.

## Next steps

- [Five-minute quick start](quickstart.md)
- [Authentication and profiles](authentication.md)
- [Agent and CI operation](agents.md)
