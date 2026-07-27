# Installation

[Documentation index](llms.txt)

Install `mammoth-cli` as an isolated command-line tool, then confirm that the
`mammoth` executable is on your PATH. Choose one installation method; do not
install the same CLI with more than one tool manager.

## Recommended: uv tool

Linux/macOS quick install:

```sh
curl -fsSL https://github.com/EdgeMetric/mammothsdk/releases/latest/download/mammoth-install.sh | sh
```

Windows PowerShell quick install:

```powershell
irm https://github.com/EdgeMetric/mammothsdk/releases/latest/download/mammoth-install.ps1 | iex
```

These one-line commands execute downloaded code. For a verified install,
download the installer and `SHA256SUMS` first, verify its SHA-256 entry and the
Sigstore bundle attached to the release, inspect the script, then execute it.

```bash
uv tool install mammoth-cli
mammoth --version
```

`uv tool` puts the `mammoth` executable on your PATH in an isolated environment.
Use `uv tool dir --bin` to find that directory.

If `mammoth` is not found after installation, open a new shell or add the tool
bin directory reported by `uv tool dir --bin` to your PATH.

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
the installer. For the direct convenience flow:

```sh
curl -fsSL https://github.com/EdgeMetric/mammothsdk/releases/latest/download/mammoth-install.sh | sh
```

```powershell
irm https://github.com/EdgeMetric/mammothsdk/releases/latest/download/mammoth-install.ps1 | iex
```

Piping a download directly to a shell does not verify it first. For the
verified flow, download the installer, `SHA256SUMS`, and
`SHA256SUMS.sigstore.json` from the release, then verify the bundle:

```bash
cosign verify-blob \
  --bundle SHA256SUMS.sigstore.json \
  --certificate-identity-regexp '^https://github\.com/EdgeMetric/mammothsdk/\.github/workflows/cli-release\.yml@refs/tags/' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  SHA256SUMS
```

The `--certificate-identity-regexp` and `--certificate-oidc-issuer`
constraints ensure the signature came from the EdgeMetric/mammothsdk release
workflow. Without them, `cosign` accepts any valid Sigstore certificate.
Then run `sha256sum --check --ignore-missing SHA256SUMS` and inspect the
installer before you execute it.

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
