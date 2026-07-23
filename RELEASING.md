# Releasing

This repository publishes two independent PyPI distributions from one codebase:

| Package | Source | PyPI | Tag prefix |
|---|---|---|---|
| `mammoth-io` (SDK) | repo root | https://pypi.org/project/mammoth-io/ | `sdk-v` |
| `mammoth-cli` (CLI) | `mammoth-cli/` | https://pypi.org/project/mammoth-cli/ | `cli-v` |

The CLI depends on `mammoth-io>=0.6.0,<0.7`, so **the SDK must be published before
the CLI**. `cli-release.yml` enforces this with a gate that fails unless the
required `mammoth-io` range already resolves on PyPI.

Each package's version lives in **two files that must stay in sync**:
`pyproject.toml` and the package's `__init__.py`.

## Preferred path — tag-triggered CI (hands-off, signed)

Pushing a version tag runs the matching release workflow, which builds
reproducibly, runs the full gate, publishes to PyPI via **Trusted Publishing**
(OIDC — no stored tokens), and (for the CLI) creates a GitHub release with
Sigstore-signed installer assets.

```bash
# 1) SDK first
git tag -a sdk-v0.6.0 -m "mammoth-io 0.6.0" <merge-commit>
git push origin sdk-v0.6.0            # -> .github/workflows/sdk-release.yml

# 2) CLI, after mammoth-io is live on PyPI
git tag -a cli-v1.0.0 -m "mammoth-cli 1.0.0" <merge-commit>
git push origin cli-v1.0.0            # -> .github/workflows/cli-release.yml
```

Both `publish` jobs use the `pypi` GitHub environment (add required reviewers
there for a manual approval gate).

### One-time PyPI setup (required for the CI path)

Trusted Publishing must be registered on PyPI **before** the first CI publish,
or the publish job fails with `invalid-publisher`:

- **mammoth-io** — on the existing project → *Manage → Publishing → Add a
  publisher*: Owner `EdgeMetric`, Repo `mm-pysdk`, Workflow `sdk-release.yml`,
  Environment `pypi`.
- **mammoth-cli** — https://pypi.org/manage/account/publishing/ → *pending
  publisher*: Project `mammoth-cli`, Owner `EdgeMetric`, Repo `mm-pysdk`,
  Workflow `cli-release.yml`, Environment `pypi`.

## Fallback path — local publish from a maintainer machine

Use only when the CI path is unavailable (e.g. Trusted Publishing not yet
configured). Requires a PyPI API token in `~/.pypirc` (`[pypi]`,
`username = __token__`). Publishing is irreversible — a version number can never
be reused.

```bash
# From a clean checkout at the release commit, in the project venv.

# --- SDK ---
rm -rf dist
SOURCE_DATE_EPOCH=1700000000 poetry build --output dist    # reproducible
twine check dist/*
twine upload dist/mammoth_io-<ver>*

# --- CLI (after the SDK resolves on PyPI) ---
cd mammoth-cli
rm -rf dist
SOURCE_DATE_EPOCH=1700000000 poetry build --output dist
twine check dist/*
twine upload dist/mammoth_cli-<ver>*
```

### GitHub releases for the installer path (local)

The one-line `curl … | sh` installer downloads the installer script from a
GitHub release, which then installs the CLI from PyPI. Cut the releases with the
built assets (installer scripts with the version substituted for
`__CLI_VERSION__`, plus wheels and `SHA256SUMS`):

```bash
cd mammoth-cli
ver=<ver>; mkdir -p release-assets
cp dist/mammoth_cli-${ver}-py3-none-any.whl dist/mammoth_cli-${ver}.tar.gz release-assets/
sed "s/__CLI_VERSION__/${ver}/g" installers/mammoth-install.sh  > release-assets/mammoth-install.sh
sed "s/__CLI_VERSION__/${ver}/g" installers/mammoth-install.ps1 > release-assets/mammoth-install.ps1
( cd release-assets && sha256sum -- * > SHA256SUMS )
gh release create cli-v${ver} --target main --title "mammoth-cli ${ver}" \
  release-assets/mammoth_cli-* release-assets/mammoth-install.* release-assets/SHA256SUMS
```

> **The repository must be public for the anonymous `curl … | sh` one-liner to
> work.** GitHub gates private-repo release assets behind authentication, so the
> unauthenticated installer URL returns `404` while the repo is private. Until
> then, install from PyPI directly: `uv tool install mammoth-cli` or
> `pipx install mammoth-cli`.
>
> The local path does not produce Sigstore signatures (those require the CI
> workflow's OIDC identity); the checksum path via `SHA256SUMS` still applies.

## Dependency lock

`mammoth-cli/poetry.lock` pins the CLI's resolved dependency tree. Regenerate it
after changing dependencies (requires the pinned `mammoth-io` to be published):

```bash
cd mammoth-cli && poetry lock && poetry check --lock
```

CI runs `poetry check --lock` so the lock never drifts from `pyproject.toml`.
