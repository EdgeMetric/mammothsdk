# Installation

[Documentation index](llms.txt)

Install `mammoth-cli` as an isolated command-line tool, then confirm that the
`mammoth` executable is on your PATH. Choose one installation method; do not
install the same CLI with more than one tool manager.

## One-line installer (recommended)

This is the shortest path and needs no prerequisites. It installs `uv` if you do
not have it, the `mammoth` CLI, and the bundled agent skill.

Linux and macOS:

```sh
curl -fsSL https://github.com/EdgeMetric/mammothsdk/releases/latest/download/mammoth-install.sh | sh
```

Windows PowerShell:

```powershell
irm https://github.com/EdgeMetric/mammothsdk/releases/latest/download/mammoth-install.ps1 | iex
```

Confirm the result:

```bash
mammoth --version
```

These one-line commands execute downloaded code. For a checksum-verified
install, download the installer and `SHA256SUMS`, verify the installer's
SHA-256 entry, inspect the script, then execute it. If the release also
attaches `SHA256SUMS.sigstore.json`, verify that bundle before trusting the
checksums; do not claim a signature when the bundle is absent.

## With uv

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
and `mammoth-install.ps1` (Windows PowerShell 5.1+). Every release attaches
`SHA256SUMS`; download the installer and that file, verify the checksum, then
inspect and run the installer. Some releases additionally attach a Sigstore
bundle. For the direct convenience flow:

```sh
curl -fsSL https://github.com/EdgeMetric/mammothsdk/releases/latest/download/mammoth-install.sh | sh
```

```powershell
irm https://github.com/EdgeMetric/mammothsdk/releases/latest/download/mammoth-install.ps1 | iex
```

Piping a download directly to a shell does not verify it first. Verify the
installer against its `SHA256SUMS` entry before execution. When the release
contains `SHA256SUMS.sigstore.json`, verify that optional bundle first:

```bash
cosign verify-blob \
  --bundle SHA256SUMS.sigstore.json \
  --certificate-identity-regexp '^https://github\.com/EdgeMetric/mammothsdk/\.github/workflows/cli-release\.yml@refs/tags/' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  SHA256SUMS
```

The `--certificate-identity-regexp` and `--certificate-oidc-issuer`
constraints ensure a present signature came from the EdgeMetric/mammothsdk
release workflow. Without them, `cosign` accepts any valid Sigstore
certificate. Then run `sha256sum --check --ignore-missing SHA256SUMS` and
inspect the installer before you execute it. If no bundle is attached, the
checksum check is not signature verification and does not authenticate the
assets unless you obtained the expected checksum through a separate trusted
channel.

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
