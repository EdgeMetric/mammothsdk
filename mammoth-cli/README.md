# mammoth-cli

A typed command-line interface for the [Mammoth Analytics](https://mammoth.io)
platform. The executable is `mammoth`.

The CLI uses the public `mammoth-io` SDK for all Mammoth requests. It does not
build a second HTTP client and does not call private SDK members.

## Status

Under active development. See `docs/plans/add-cli-for-mammoth.md` in the
repository root for the full plan.

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
