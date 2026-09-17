# Installation

[Documentation index](llms.txt)

Install `mammoth-cli` as an isolated command-line tool, then confirm that the
`mammoth` executable is on your PATH. Choose one installation method; do not
install the same CLI with more than one tool manager.

## PyPI with uv (recommended)

Install the published 1.1.12 CLI into an isolated environment:

```bash
uv tool install mammoth-cli==1.1.12
```

Confirm the result:

```bash
mammoth --version
```

`uv tool` puts the `mammoth` executable on your PATH in an isolated environment.
Use `uv tool dir --bin` to find that directory.

If `mammoth` is not found after installation, open a new shell or add the tool
bin directory reported by `uv tool dir --bin` to your PATH.

## From PyPI with pip

```bash
python -m pip install mammoth-cli==1.1.12  # Python 3.12, 3.13, or 3.14
mammoth --version
```

The CLI supports Python 3.12 through the latest tested stable minor (currently
3.12, 3.13, and 3.14). It does not support 3.10 or 3.11.

## From PyPI with pipx

```bash
pipx install mammoth-cli==1.1.12
mammoth --version
```

`pipx` installs the `mammoth` executable in an isolated environment and puts it
on your PATH. Run `pipx upgrade mammoth-cli` to update it.

## GitHub release installers (conditional)

The local-built 1.1.12 release has no GitHub release installer assets,
`SHA256SUMS`, or Sigstore bundle. Do not use a `releases/latest` installer URL
for it. If a future release explicitly attaches installers and `SHA256SUMS`,
download a versioned asset, verify its checksum, inspect it, then execute it.
If that release also attaches `SHA256SUMS.sigstore.json`, verify the optional
bundle first:

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
inspect the installer before execution. Without a bundle, a checksum check is
not signature verification and needs a separate trusted checksum source.

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
