# mammoth-cli

A typed command-line interface for the [Mammoth Analytics](https://mammoth.io)
platform. The executable is `mammoth`.

The CLI uses the public `mammoth-io` SDK for all Mammoth requests. It does not
build a second HTTP client and does not call private SDK members.

## Status

Stable. `mammoth-cli` 1.0.0 is a production release; the command surface and the
machine-output contract are covered by the compatibility policy below.

## Versioning & support

`mammoth-cli` follows [Semantic Versioning](https://semver.org) for the 1.x
series. Within the 1.x major line:

- The machine-output and error-envelope contract is stable. `SCHEMA_VERSION`
  (see `mammoth_cli/__init__.py`) identifies that contract and does not change
  incompatibly within a major version; new fields may be added, but existing
  fields and their meanings are preserved.
- The CLI surface is stable: command names, subcommands, flags, and exit codes
  are not removed or repurposed. New commands, flags, and output fields may be
  added in minor releases.
- Bug fixes ship in patch releases; additive, backward-compatible changes ship
  in minor releases.

Any breaking change to the machine-output contract or the CLI surface bumps the
major version (2.0.0).

## Layout

| Path | Purpose |
|---|---|
| `mammoth_cli/` | CLI package (`app`, `commands`, `contracts`, `services`, `context`, `output`, `errors`, `manifest`, `skills`, `messages`). |
| `spec/openapi/` | Pinned production OpenAPI snapshot and metadata. |
| `spec/manifests/` | Reviewed parity manifests: operations, SDK methods, commands, and the schema. |
| `spec/reports/` | Generated parity report and expected red-first baseline. |
| `scripts/` | Deterministic build scripts (offline, no login). |
| `tests/` | Contract, unit, subprocess, and guarded live tests. |

## Reproducing the manifests

```bash
python scripts/sync_openapi.py --check    # verify the pinned snapshot digest
python scripts/build_manifests.py         # regenerate the three manifests
python scripts/build_parity_report.py     # regenerate spec/reports/parity.md
```

Refreshing the pinned snapshot from the network is an explicit maintenance
operation (`python scripts/sync_openapi.py`); ordinary CI never fetches it.

## Development

```bash
pytest tests/ -q                 # unit + contract tests (live tests deselected)
ruff check mammoth_cli scripts tests
black mammoth_cli scripts tests
mypy mammoth_cli
```

## Releasing

The CLI and its `mammoth-io` SDK dependency publish from independent,
tag-triggered workflows (`cli-v*` / `sdk-v*`); the SDK must publish first. The
full process — tag-triggered CI (Trusted Publishing + Sigstore-signed installer
assets), one-time PyPI setup, the local fallback, and the dependency lock — is
documented in [../RELEASING.md](../RELEASING.md).

`poetry.lock` pins the resolved dependency tree; CI runs `poetry check --lock`
to keep it consistent with `pyproject.toml`.
