# Normative appendix: SDK client and AI command catalog

This appendix completes the reviewed command disposition for the eleven public
SDK methods not owned by the resource, view/transformation, or I/O catalogs.
Together, plans 09, 10, 11, and 14 cover all 242 methods in plan 13. Convenience
methods map to one canonical handler. They do not create duplicate handlers.

Each AI command must support the global project context, `--input FILE|-`,
`--output json`, and `--no-input`. A command must resolve a view's dataset by
using a public typed SDK method. The dataset ID is not a CLI argument. All
request documents reject unknown fields. Prompts and intents must be nonempty
after trimming. Machine results use the common result envelope from plan 02.

Policy cells have this order: **wait; rollback; safety; live acceptance**.
`always_wait` waits through the SDK job seam. `none` makes no rollback promise.
AI operations must state in help that data can be processed by an AI feature.
Do not infer addon availability from an authorization error.

## `mammoth.api.ai.AIAPI`

| Exact public signature | Canonical command and exact local input | Typed result and policy | Required tests and blocker |
|---|---|---|---|
| `generate_profile(dataview_id: int, dataset_id: int \| None = None) -> dict[str, Any]` | `view ai profile VIEW_ID`; no local options | `AIProfileResult`; `always_wait; none; benign_mutation; live_disposable_project` | `UT-AI-PROFILE`, `CT-AI-PROFILE-JSON`, `CT-AI-PROFILE-WAIT`, `CT-AI-PROFILE-ERROR`, `LT-AI-PROFILE`; A1, A2 |
| `generate_data(dataview_id: int, prompt: str, no_of_rows: int = 10, columns: list[str] \| None = None, dataset_id: int \| None = None) -> dict[str, Any]` | `view ai generate-data VIEW_ID --prompt TEXT [--rows 10] [--column TEXT]...`; rows are 1 through 100; columns are unique and nonempty | `AIGeneratedDataResult`; `always_wait; none; benign_mutation; live_disposable_project` | `UT-AI-GENERATE-DATA`, `CT-AI-GENERATE-DATA-JSON`, `CT-AI-GENERATE-DATA-WAIT`, `CT-AI-GENERATE-DATA-ERROR`, `LT-AI-GENERATE-DATA`; A1, A2, A3 |
| `get_data_gen_info(dataview_id: int, dataset_id: int \| None = None) -> dict[str, Any]` | `view ai generation-info VIEW_ID`; no local options | `AIDataGenerationInfoResult`; `not_async; none; read; live_disposable_project` | `UT-AI-GENERATION-INFO`, `CT-AI-GENERATION-INFO-JSON`, `CT-AI-GENERATION-INFO-ERROR`, `LT-AI-GENERATION-INFO`; A1, A2 |
| `generate_sql(intent: str, sequence_number: int = 0) -> dict[str, Any]` | `ai sql generate --intent TEXT [--sequence 0]`; sequence is a nonnegative integer | `AIGeneratedSqlResult`; `always_wait; none; read; live_disposable_project` | `UT-AI-SQL-GENERATE`, `CT-AI-SQL-GENERATE-JSON`, `CT-AI-SQL-GENERATE-WAIT`, `CT-AI-SQL-GENERATE-ERROR`, `LT-AI-SQL-GENERATE`; A2, A3 |
| `get_suggestions() -> dict[str, Any]` | `ai suggestion list`; no local options | `AISuggestionListResult`; `always_wait; none; read; live_disposable_project` | `UT-AI-SUGGESTION-LIST`, `CT-AI-SUGGESTION-LIST-JSON`, `CT-AI-SUGGESTION-LIST-WAIT`, `CT-AI-SUGGESTION-LIST-ERROR`, `LT-AI-SUGGESTION-LIST`; A2, A3 |
| `query_gen(connector_key: str, connection_key: str, prompt: str, project_id: int \| None = None) -> dict[str, Any]` | `connector query generate CONNECTOR_KEY CONNECTION_KEY --prompt TEXT`; keys are nonempty and cannot contain `/` | `AIGeneratedConnectorQueryResult`; `always_wait; none; read; external_fixture` | `UT-CONNECTOR-QUERY-GENERATE`, `CT-CONNECTOR-QUERY-GENERATE-JSON`, `CT-CONNECTOR-QUERY-GENERATE-WAIT`, `CT-CONNECTOR-QUERY-GENERATE-ERROR`, `LT-CONNECTOR-QUERY-GENERATE`; A2, A3, A4 |

`generate_data` is a preview operation in the pinned OpenAPI document. It must
not claim that it writes generated rows to the view. `generate_sql` returns a
query and metadata. It differs from `view transform generate-sql`, which adds
and executes a pipeline task. The command names and help must preserve this
difference.

## `mammoth.client.MammothClient`

| Exact public signature | Disposition | Canonical behavior and test |
|---|---|---|
| `find_dataset_for_dataview(dataview_id: int) -> int` | `alias` | Used by the public view resolver. `view get VIEW_ID` exposes `dataset_id`; no network-duplicating command. Test `UT-CLIENT-FIND-DATASET-ALIAS` and a multi-page resolver case. |
| `set_project_id(project_id: int) -> None` | `alias` | Global `--project PROJECT_ID` sets per-process context. `context project use PROJECT_ID` saves context for the selected profile; `context project clear` removes it; `context project status` reads it. Test `UT-CONTEXT-PROJECT`, `CT-CONTEXT-PROJECT-JSON`, and cross-process persistence. |
| `test_connection() -> bool` | `alias` | `auth status --check` uses a typed diagnostic that distinguishes invalid credentials, forbidden workspace, server unavailability, and timeout. Do not implement the SDK method's lossy boolean behavior in the CLI. Test `UT-AUTH-CHECK-ERROR-MAPPING` and `CT-AUTH-STATUS-CHECK-JSON`. |
| `get_view(view_id: int) -> View` | `alias` | `view get VIEW_ID`; test `UT-CLIENT-GET-VIEW-ALIAS`. |
| `branch_out(view_id: int, dataset_name: str, *, target_ds_id: int \| None = None, column_mapping: dict[str, str] \| None = None, **kwargs: Any) -> int` | `alias` | `view export dataset VIEW_ID` with the complete typed contract in plan 10. Never expose `**kwargs`; test `UT-CLIENT-BRANCH-OUT-ALIAS`. |

Saved project context is operational configuration, not authentication. Its
profile record can contain only a positive project ID. Environment-based auth
does not write this value implicitly. `--project` always wins for one process.

## Blockers and required SDK work

| ID | Required resolution before the command is implemented |
|---|---|
| `A1` | Add one public typed view-to-dataset resolver. It must paginate safely and distinguish not found, duplicate/inconsistent ownership, forbidden, and server failure. |
| `A2` | Replace raw dictionaries with public request and result models. Preserve job identity, sequence, validation details, generated SQL, suggestions, profile fields, and unknown forward-compatible payload data in one documented extension field. |
| `A3` | Prove AI addon behavior and final job states in the disposable live fixture. If the addon is unavailable, keep contract tests and mark the guarded live case skipped with a machine-readable reason. |
| `A4` | Provision a dedicated connector fixture. Redact connector credentials and prompt-derived secrets from debug output, error details, snapshots, and ledgers. Never send a live connector query without that fixture. |

## Completeness and acceptance

- Method rows in this appendix: `11` (`6` AI and `5` client methods).
- Every row has one disposition and one canonical command or behavior.
- Every canonical AI command receives human-output, JSON-output, validation,
  timeout, redaction, and API-error contract tests as applicable.
- Capability and schema discovery must return each canonical command, its exact
  input model, enum values, safety class, wait policy, and recovery commands.
- Low-context agent tests must discover and run an AI read command from
  `mammoth capability` and `mammoth schema` without reading Python source.
