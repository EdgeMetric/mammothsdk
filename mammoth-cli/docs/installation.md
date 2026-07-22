# Installation

[Documentation index](llms.txt)

## Recommended: uv tool

```bash
uv tool install mammoth-cli
mammoth --version
```

`uv tool` puts the `mammoth` executable on your PATH in an isolated environment.
Use `uv tool dir --bin` to find that directory.

## From PyPI with pip

```bash
python -m pip install mammoth-cli      # Python 3.12, 3.13, or 3.14
mammoth --version
```

The CLI supports Python 3.12 through the latest tested stable minor (currently
3.12, 3.13, and 3.14). It does not support 3.10 or 3.11.

## From PyPI with pipx

```bash
pipx install mammoth-cli
mammoth --version
```

`pipx` installs the `mammoth` executable in an isolated environment and puts it
on your PATH. Run `pipx upgrade mammoth-cli` to update it.

## Convenience installers

The versioned release ships `mammoth-install.sh` (Linux and macOS, POSIX `sh`)
and `mammoth-install.ps1` (Windows PowerShell 5.1+). The verified flow downloads
the installer, `SHA256SUMS`, and the Sigstore bundle, verifies both, then runs
the installer. See the release notes for the exact `cosign verify-blob` command.

## Install the agent skill

```bash
mammoth skill install --output json --no-input          # all agents, user scope
mammoth skill path --output json --no-input             # show source + targets
mammoth skill list --output json --no-input
```

The skill installs for Codex, Claude Code, and Cursor. Pass an `--input`
document with `{"agents": ["claude"], "scope": "project"}` to narrow the target.

## Next steps

- [Five-minute quick start](quickstart.md)
- [Authentication and profiles](authentication.md)
