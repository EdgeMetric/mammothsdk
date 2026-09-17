# Releasing

This repository publishes two independent PyPI distributions from one codebase:

| Package | Source | PyPI | Tag prefix |
|---|---|---|---|
| `mammoth-io` (SDK) | repo root | https://pypi.org/project/mammoth-io/ | `sdk-v` |
| `mammoth-cli` (CLI) | `mammoth-cli/` | https://pypi.org/project/mammoth-cli/ | `cli-v` |

The CLI depends on `mammoth-io>=0.7.1,<0.8`, so **the SDK must be published before
the CLI**. `cli-release.yml` enforces this with a gate that fails unless the
required `mammoth-io` range already resolves on PyPI.

Each package's version lives in **two files that must stay in sync**:
`pyproject.toml` and the package's `__init__.py`.

The CLI's release metadata is now PEP 621 in `mammoth-cli/pyproject.toml` and
its build backend is Hatchling. The CI workflow and checked-in lockfile are
still Poetry-based during this migration; keep the commands below aligned with
CI until that migration is completed.

## Preferred path — tag-triggered CI (hands-off, signed)

Pushing a version tag runs the matching release workflow, which builds
reproducibly, runs the full gate, publishes to PyPI via **Trusted Publishing**
(OIDC — no stored tokens), and (for the CLI) creates a GitHub release with
Sigstore-signed installer assets.

```bash
# 1) SDK first
git tag -a sdk-vX.Y.Z -m "mammoth-io X.Y.Z" <merge-commit>
git push origin sdk-vX.Y.Z            # -> .github/workflows/sdk-release.yml

# 2) CLI, after mammoth-io is live on PyPI
git tag -a cli-vX.Y.Z -m "mammoth-cli X.Y.Z" <merge-commit>
git push origin cli-vX.Y.Z            # -> .github/workflows/cli-release.yml
```

Both `publish` jobs use the `pypi` GitHub environment (add required reviewers
there for a manual approval gate).

### Current automation state

GitHub Actions are currently disabled repository-wide at the release owner's
request. This pauses all CI and release workflows; do not infer CI validation,
CI-built artifacts, GitHub release assets, or signing from releases made while
it is disabled. Re-enable only with explicit approval. Repository-wide
reenablement does not restore workflows that were separately disabled. After
the repository setting is restored, the owner must separately restore these
five CLI workflows: CLI CI (`318853564`), CLI Release (`318853565`), Lint
(`318853566`), OpenAPI drift (`318853567`), and Tests (`318853571`).

```bash
# First restore repository-wide Actions.
gh api -X PUT repos/EdgeMetric/mammothsdk/actions/permissions \
  -H 'Accept: application/vnd.github+json' \
  --input <(printf '{"enabled":true}')

# Then restore each individually disabled CLI workflow.
gh workflow enable 318853564
gh workflow enable 318853565
gh workflow enable 318853566
gh workflow enable 318853567
gh workflow enable 318853571
```

### One-time PyPI setup (required for the CI path)

Trusted Publishing must be registered on PyPI **before** the first CI publish,
or the publish job fails with `invalid-publisher`:

The `sdk-v0.7.0` CI publish received `invalid-publisher` on 2026-09-17;
its build/verify job passed and the exact verified artifacts were published
with the documented local Twine fallback. Register the publishers below
before relying on unattended CI publication. Never treat a successful build
job as proof that PyPI accepted the package.

- **mammoth-io** — on the existing project → *Manage → Publishing → Add a
  publisher*: Owner `EdgeMetric`, Repo `mammothsdk`, Workflow `sdk-release.yml`,
  Environment `pypi`.
- **mammoth-cli** — https://pypi.org/manage/account/publishing/ → *pending
  publisher*: Project `mammoth-cli`, Owner `EdgeMetric`, Repo `mammothsdk`,
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

CI runs `poetry check --lock` so the lock stays synchronized with the package
metadata while the PEP 621/Hatch migration is completed.
