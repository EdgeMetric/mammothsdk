# Mammoth Python SDK - Key Patterns

## Project Structure
- SDK root: `mammoth/` with `api/`, `models/`, `utils/` subpackages
- Main client: `mammoth/client.py` — `MammothClient` with 16 sub-clients
- Key new files: `condition.py`, `view.py`, `api/pipeline.py`, `models/pipeline.py`
- Reference files: `mvc-service/api/api/mmllm/intent_engine/` for transformation payloads

## API Sub-Client Pattern
- All API classes take `client` in `__init__`, store as `self._client`
- Use `self._client.workspace_id` for workspace ID (attribute, not method)
- Use `self._client.project_id` via `getattr(self._client, 'project_id', None)`
- Consistent verb naming: `list()`, `get()`, `create()`, `update()`, `delete()`

## Key Design Decisions
- `client.views.get(id)` returns rich `View` objects (not raw dicts)
- `Condition` class supports `&` (AND) and `|` (OR) Python operators
- Conditions build to API format: `{"AND": [{"column_1": {"GTE": {"VALUE": 1000}}}]}`
- ViewExport accessible via `view.export.to_csv()`, `view.export.to_postgres()`
- No backward-compat aliases — all methods renamed for consistency

## Transformation Task Keys
SET, SELECT, MATH, SQL, COPY, DELETE, ADD_COLUMN, COMBINE, REPLACE, CONVERT,
TEXT_TRANSFORM, SPLIT, JOIN, PIVOT, WINDOW, EXTRACT_DATE, DATE_DIFF,
INCREMENT_DATE, FILL, LIMIT, LOOKUP, SUBSTRING, UNNEST, JSON_HANDLE, GEN_AI, CROSSTAB
