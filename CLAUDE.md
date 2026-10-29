# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Monorepo for the [Mammoth Analytics](https://mammoth.io) client stack. Three packages, each released to PyPI:

| Dir | Package | What |
|-----|---------|------|
| `mammoth/` | `mammoth-io` | Python SDK: REST sub-clients, rich `View` objects, `Condition` builders, export helpers |
| `mammoth-cli/` | `mammoth-cli` | `mammoth` CLI on top of the SDK; manifest-driven (`spec/manifests/`), typer |
| `mammoth-mcp-server/` | `mammoth-mcp-server` | MCP server on top of the SDK |

The CLI and MCP server import the in-repo SDK, so an SDK change can break them: run their checks too.

## Commands

```bash
# Setup (CI uses uv; the dev tools are the `dev` dependency group)
uv venv && uv pip install -e . --group dev                    # SDK
cd mammoth-cli && uv pip install -e .. -e . --group dev       # CLI (same for mammoth-mcp-server)

# SDK checks (run from the repo root)
black -t py312 mammoth/ tests/ && ruff check mammoth/ && mypy mammoth/ && pytest tests/unit/ -q -n auto
pytest tests/unit/test_transformations.py::TestMath -v        # one class
pytest tests/integration/ -v                                  # live API, needs credentials

# CLI checks (run from mammoth-cli/); the suite is slow, so run the touched test files first
black --check -t py312 mammoth_cli/ tests/ scripts/ && ruff check mammoth_cli/ tests/ scripts/ && mypy mammoth_cli/
pytest tests -m "not live and not fuzz and not subprocess" -q -n auto

# MCP server checks (run from mammoth-mcp-server/)
ruff check . && mypy mammoth_mcp_server/ && pytest tests -q -n auto
```

`.github/workflows/pr-checks.yml` is the source of truth for these commands. It runs the tests on Python 3.12 and 3.14, and lint and types on 3.12 only. `pytest -m fuzz` (about 20 minutes) and `pytest -m live` (needs `MAMMOTH_EVAL_TOKEN_FILE` and `MAMMOTH_SERVER_PREFIX`) are opt-in. `-n auto` (pytest-xdist, in every `dev` group) runs the tests in parallel: the CLI suite drops from about 10 minutes to under 3. Drop it to debug a single failure.

## Architecture

### Core classes
- **MammothClient** (`mammoth/client.py`) — entry point; authenticates with `api_token` (Bearer `mm_...`), `api_key`+`api_secret` or a `token_provider`, and looks the workspace up on first use (`workspace_id=` is an optional hint that skips the lookup). `views` is built eagerly; the other sub-clients (the `SUB_CLIENTS` table: projects, datasets, pipeline, exports, support, ...) are created on first attribute access
- **View** (`view.py`) — rich domain object wrapping a dataview; 25+ transformation methods organized via **mixin pattern** in `_mixins/`; metadata accessed via `view.display_names`, `view.column_types`, `view.columns`
- **Condition** (`condition.py`) — filter builder with `&` (AND), `|` (OR), `~` (NOT) operator overloading
- **ViewExport** (`view.py`) — export helper: `view.export.to_csv()`, `to_postgres()`, `to_s3()`, etc.

### Key flow: transformations
1. Transformation method (e.g. `view.filter_rows()`) builds a task spec dict
2. Calls `self._add_task(spec)` → `POST /pipeline/add_task`
3. Polls job until completion (async pipeline tasks)
4. Refreshes view metadata on success
5. Returns API response dict

### Column name resolution
All methods accept **display names** (user-friendly). The SDK auto-resolves to internal names (e.g. `"column_qklgqhtw6v"`) via `_resolve_column()`. Missing names raise `MammothColumnError`.

### Mixin organization (`_mixins/`)
| File | Methods |
|------|---------|
| `_filter_ops.py` | filter_rows, set_values |
| `_math_ops.py` | math |
| `_column_ops.py` | add_column, delete_columns, copy_columns, combine_columns, convert_type, rename_columns |
| `_text_ops.py` | text_transform, replace_values, bulk_replace, split_column, substring |
| `_date_ops.py` | extract_date, date_diff, increment_date |
| `_aggregate_ops.py` | pivot, window, crosstab |
| `_row_ops.py` | fill_missing, limit_rows, discard_duplicates, unnest, sort_rows |
| `_advanced_ops.py` | join, lookup, json_extract, gen_ai, generate_sql, add_sql |

### Other key files
- `mammoth/_pure/builders.py` — per-operation payload builders (`build_<op>_params`); the mixins call these, and `builders.py` re-exports them publicly
- `_param_templates.py` — standalone copy of the backend's param_templates; no SDK code imports it (only `tests/unit/test_transformations.py`), so use it as a payload-format reference
- `_expression_parser.py` — math string expression → token list parser
- `models/pipeline.py` — all enums (Operator, ColumnType, JoinType, etc.) and dataclasses (SetValue, CopySpec, etc.)
- `mammoth/api/` — REST API sub-clients (CRUD operations), one module per area
- `exceptions.py` — MammothError hierarchy (MammothAPIError, MammothAuthError, MammothColumnError, MammothTransformError, MammothJobTimeoutError, MammothJobFailedError)

## Adding a New Transformation

1. Add method to the appropriate mixin in `mammoth/_mixins/`
2. Add dataclass to `mammoth/models/pipeline.py` if structured params needed
3. Add a `build_<op>_params` function to `mammoth/_pure/builders.py` (re-export it from `mammoth/builders.py`); the mixin method calls it
4. Export new types from `mammoth/__init__.py`
5. Add unit test to `tests/unit/test_transformations.py`
6. Add integration test to `tests/integration/test_transformations.py`

## CLI: adding a command or covering a new API operation

- A command is a `command_id` (e.g. `support.workspace.get`) mapped in `mammoth-cli/mammoth_cli/commands/registry.py` to `"module:function"`, plus a manifest record.
  - `scripts/build_manifests.py` generates a record for every operation-backed or SDK-catalog command into `spec/manifests/commands.generated.yaml`. Never edit that file.
  - `spec/manifests/commands/<group>.yaml` holds only the fields that differ from the generated record (plus `unset`, a list of generated fields to drop), or the full record of a command the generator doesn't make. The loader merges the two.
- Every operation in the pinned prod OpenAPI spec has a row in `spec/manifests/openapi-operations.yaml` with a `disposition`. `unmapped` means a real gap.
  - Cover a gap with an SDK method plus a CLI command.
  - If no terminal user should drive the operation, add it with a reason to `INTERNAL_ONLY` or `PROTOCOL_ONLY` in `scripts/_command_map.py`.
- Regenerate after any change, from `mammoth-cli/`. Re-running must produce no diff, and contract tests fail on stale output.
  - `scripts/build_manifests.py`: it also compiles the manifests to the JSON the CLI reads. Run `scripts/compile_manifests.py` alone only after hand-editing a manifest.
  - `scripts/generate_release_capability_matrix.py` (see `mammoth-cli/docs/capability-drift-workflow.md`).
  - `scripts/build_parity_report.py`.
  - `scripts/gen_docs.py`.
- Live check: `mammoth --profile <name> ...` against a dev server, never prod, unless the change is read-only.

## Releasing the MCP server

The `release-sync` skill checks and fixes every release surface. These are the MCP server steps, in order:

1. **Bump the version.** Change it in `mammoth-mcp-server/pyproject.toml`, `mammoth-mcp-server/mammoth_mcp_server/__init__.py` and `mammoth-mcp-server/server.json` together; a test fails if they differ. Add the CHANGELOG entry. Merge the PR.
2. **Publish to PyPI** (there is no CI workflow for it).
   - Test: `cd mammoth-mcp-server && uv run --with-editable . --with pytest --with pytest-asyncio --with ../ python -m pytest tests -q`.
   - Build: `SOURCE_DATE_EPOCH=1700000000 uv build --out-dir <scratch>`.
   - Upload: `uvx twine check <scratch>/*`, then `uvx twine upload -r pypi --non-interactive <scratch>/*`.
3. **Tag and release.**
   - `git tag -a mcp-server-vX -m "mammoth-mcp-server X" <merge commit> && git push origin mcp-server-vX`.
   - `gh release create mcp-server-vX --verify-tag --latest=false` with the wheel and sdist downloaded from PyPI, not rebuilt.
4. **Deploy.** Deploy the new version to `https://mcp.mammoth.io/mcp`. Ops does this; it isn't in this repo. Check that `https://mcp.mammoth.io/.well-known/mcp/server-card.json` reports the new version.
5. **Publish to the MCP registry** (`io.mammoth/mcp`), after step 4.
   - Each version publishes once and can't be changed, and clients connect to the URL in `server.json`.
   - Log in with the DNS key:
     ```bash
     cd mammoth-mcp-server
     PRIVATE_KEY="$(openssl pkey -in ~/.config/mammoth/mcp-registry-key.pem -noout -text | grep -A3 'priv:' | tail -n +2 | tr -d ' :\n')"
     mcp-publisher login dns --domain mammoth.io --private-key "$PRIVATE_KEY"
     ```
   - Then run `mcp-publisher validate && mcp-publisher publish`.
   - Verify: `curl -s https://registry.modelcontextprotocol.io/v0/servers/io.mammoth%2Fmcp/versions` lists the version as latest.
   - Key setup and the `mammoth.io` DNS TXT record are documented in `mm-ai-docs/deploy/README.md`.
   - Never commit, print or paste the private key.

## Conventions

- All enums extend `str, Enum` — serialize as strings in JSON, work with IDE autocomplete
- **Every user-visible change adds a `CHANGELOG.md` entry under `## [Unreleased]` in the same PR**, in the matching `### Added/Changed/Deprecated/Removed/Fixed (next <packages>)` section. Tests, CI and refactors with no behaviour change may skip it. On publish, move everything under `[Unreleased]` to the new release heading (`## mammoth-io X, mammoth-cli Y, mammoth-mcp-server Z (YYYY-MM-DD)`, with each `### ... (next ...)` rewritten to name its version) and leave `## [Unreleased]` empty
- Version is set in **two places** (keep in sync): `pyproject.toml` and `mammoth/__init__.py` (CLI: `mammoth-cli/`, MCP server: `mammoth-mcp-server/`, same pair per package; the MCP server also has `mammoth-mcp-server/server.json`). They cannot be merged: Poetry 2 rejects a dynamic `[project] version` (`poetry version`/`check`/`build` run in the release workflows), and `importlib.metadata` goes stale in editable/`PYTHONPATH` checkouts and costs start-up time. Per-package unit tests and `scripts/release_status.py` fail when the two differ
- Line length: 100 (black + ruff)
- Python target: 3.12–3.14 (`from __future__ import annotations` used throughout)
- mypy strict mode with overrides for `api/` (return-value), `_mixins/` (attr-defined), and `view` (return-any)
- Backend reference code lives in the sibling `mvc-service` checkout (not in this repo) (param_templates, constants) — useful for verifying payload formats
- Upload types numbers and ISO dates (`2026-01-31`) on its own; other date formats and number columns with text (`N/A`) upload as TEXT and need `convert_type` before date or math operations. Never convert a column to the type it already has: the pipeline goes to `ref_error` (verified on release, 2026-09-25)
- `FillDirection.FIRST_VALUE` is the forward fill (previous row); `LAST_VALUE` is the back-fill (next row)
- Format with `-t py312` (the configured target). Black targeting py314 rewrites `except (A, B):` to `except A, B:`, a syntax error on 3.12; `tests/unit/test_py312_syntax.py` guards the SDK and CLI
- Subscription connectors no longer take `price_per_month` (`connector_create`/`connector_update` warn and drop it); features and feature profiles still send it. `PipelineAPI.preview_task` accepts `sample_size` only in 1..500
