# Installation

[Documentation index](llms.txt)

Install `mammoth-cli` as an isolated command-line tool, then confirm that the
`mammoth` executable is on your PATH. The supported user-facing path bootstraps
its own `uv` tool environment when needed; it requires curl, bash, and network
access. It installs both the CLI and bundled agent skill by default.

## Install

Run:

```bash
curl -fsSL https://raw.githubusercontent.com/EdgeMetric/mammothsdk/main/mammoth-cli/installers/mammoth-install.sh | bash
```

Confirm the result:

```bash
mammoth --version
```

If `mammoth` is not found after installation, open a new shell so the
installer's tool bin directory is on your PATH.

### Pinning and automation

The bare command intentionally installs the installer’s release-selected
version. Use `--version X.Y.Z` only when a release record, test, or deployment
requires an exact artifact. The installer has no normal prompts, so
`--noninteractive` is not needed.

```bash
curl -fsSL https://raw.githubusercontent.com/EdgeMetric/mammothsdk/main/mammoth-cli/installers/mammoth-install.sh | bash -s -- --version X.Y.Z
```

Use the SDK’s separate `pip` installation below for Python application code;
do not use `pip` or a preinstalled tool manager as the primary CLI install
path.

### Verified release install

The convenience command above executes a downloaded script. When an exact
release requires artifact verification, download its release assets first,
verify the signed checksum manifest, check the installer hash, inspect the
local script, and only then run it. Replace `cli-vX.Y.Z` with the approved tag:

```bash
curl -fLO https://github.com/EdgeMetric/mammothsdk/releases/download/cli-vX.Y.Z/mammoth-install.sh
curl -fLO https://github.com/EdgeMetric/mammothsdk/releases/download/cli-vX.Y.Z/SHA256SUMS
curl -fLO https://github.com/EdgeMetric/mammothsdk/releases/download/cli-vX.Y.Z/SHA256SUMS.sigstore.json
cosign verify-blob --bundle SHA256SUMS.sigstore.json \
  --certificate-identity-regexp '^https://github\\.com/EdgeMetric/mammothsdk/\\.github/workflows/cli-release\\.yml@refs/tags/' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' SHA256SUMS
sha256sum --check --ignore-missing SHA256SUMS
sh ./mammoth-install.sh
```

The certificate identity and issuer constraints bind the checksum manifest to
the EdgeMetric release workflow; a bare Sigstore verification would accept a
manifest signed by any valid identity. The exact tag and installer checksum
must be present in the verified manifest before execution.

## SDK installation

The Python SDK remains independently installable with pip:

```bash
python -m pip install mammoth-io==0.7.3
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
