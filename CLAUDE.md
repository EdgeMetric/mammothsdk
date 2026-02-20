# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**mammoth-io** — Python SDK for the [Mammoth Analytics](https://mammoth.io) platform. Wraps the REST API with rich View objects, operator-overloaded condition builders, and export helpers. Published to PyPI as `mammoth-io`.

## Commands

```bash
# Setup
poetry install                    # or: pip install -e ".[dev]"

# Tests
pytest tests/unit/ -v             # unit tests only (~2s, no API calls)
pytest tests/integration/ -v      # live API tests (requires credentials)
pytest tests/unit/test_transformations.py::TestMath -v  # single test class

# Lint & format
black mammoth/ tests/             # format
ruff check mammoth/               # lint (add --fix to auto-fix)
mypy mammoth/                     # type check (strict mode)

# All checks before commit
black mammoth/ tests/ && ruff check mammoth/ && mypy mammoth/ && pytest tests/unit/ -q
```

## Architecture

### Core classes
- **MammothClient** (`client.py`) — entry point; authenticates via api_key + api_secret + workspace_id; exposes 23 sub-clients as attributes (views, projects, datasets, pipeline, exports, etc.)
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
| `_column_ops.py` | add_column, delete_columns, copy_columns, combine_columns, convert_type |
| `_text_ops.py` | text_transform, replace_values, bulk_replace, split_column, substring |
| `_date_ops.py` | extract_date, date_diff, increment_date |
| `_aggregate_ops.py` | pivot, window, crosstab |
| `_row_ops.py` | fill_missing, limit_rows, discard_duplicates, unnest |
| `_advanced_ops.py` | join, lookup, json_extract, gen_ai, generate_sql, add_sql |

### Other key files
- `_param_templates.py` — low-level payload builders for all task types
- `_expression_parser.py` — math string expression → token list parser
- `models/pipeline.py` — all enums (Operator, ColumnType, JoinType, etc.) and dataclasses (SetValue, CopySpec, etc.)
- `api/` — 23 REST API sub-clients (CRUD operations)
- `exceptions.py` — MammothError hierarchy (MammothAPIError, MammothAuthError, MammothColumnError, MammothTransformError, MammothJobTimeoutError, MammothJobFailedError)

## Adding a New Transformation

1. Add method to the appropriate mixin in `mammoth/_mixins/`
2. Add dataclass to `mammoth/models/pipeline.py` if structured params needed
3. Add payload builder to `mammoth/_param_templates.py`
4. Export new types from `mammoth/__init__.py`
5. Add unit test to `tests/unit/test_transformations.py`
6. Add integration test to `tests/integration/test_transformations.py`

## Conventions

- All enums extend `str, Enum` — serialize as strings in JSON, work with IDE autocomplete
- Version is set in **two places** (keep in sync): `pyproject.toml` and `mammoth/__init__.py`
- Line length: 100 (black + ruff)
- Python target: 3.10+ (`from __future__ import annotations` used throughout)
- mypy strict mode with overrides for `api/` (return-value), `_mixins/` (attr-defined), and `view` (return-any)
- Backend reference code lives in `mvc-service/` (param_templates, constants) — useful for verifying payload formats
- CSV date columns upload as TEXT — must `convert_type` before date operations
