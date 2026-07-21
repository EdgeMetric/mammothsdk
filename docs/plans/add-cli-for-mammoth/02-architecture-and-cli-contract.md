# Architecture and CLI contract

## Toolchain

Use these current versions as the initial lock targets. Recheck them when the
lockfile is created, and record any required change in the audit ledger.

| Package | Initial range | Purpose |
|---|---:|---|
| Typer | `>=0.27,<0.28` | Typed command tree and completion |
| Rich | `>=15,<16` | Human terminal presentation only |
| platformdirs | `>=4.10,<5` | Native configuration locations |
| tomlkit | `>=0.15.1,<0.16` | Preserved TOML profiles |
| keyring | `>=25.7,<26` | OS credential storage |
| PyYAML | `>=6,<7` | Safe YAML input |
| Pydantic | `>=2.13,<3` | Strict command and SDK contracts |
| datamodel-code-generator | `>=0.69,<0.70` | Reproducible OpenAPI wire models |
| poetry-core | `>=2.4,<3` | PEP 517 build backend |
| uv | `0.11.30` | Pinned quick-installer bootstrap target |

These versions were verified against PyPI on 2026-07-21. Recheck all direct
dependencies when the lockfile is created. Record the inspected version,
release date, Python requirement, and reason for any different selection in
the audit ledger. Do not update a dependency without its unit, package, and
installer tests.

Do not use Click internals or add an independent incompatible Click constraint.
Use Typer's public API and its resolved Click dependency.

## Package layers

Create these logical layers under `mammoth-cli`:

- `app`: root Typer application and global options.
- `commands`: resource command groups with no transport logic.
- `contracts`: Pydantic command requests, results, metadata, and errors.
- `services`: typed protocols and the SDK-backed implementation.
- `context`: profile, endpoint, authentication, and project resolution.
- `output`: recursive normalization and human/machine rendering.
- `errors`: exception classification, redaction, and exit mapping.
- `manifest`: loaded command and parity records.
- `skills`: bundled skill data and installation logic.
- `messages`: reviewed user-facing terminology and recovery hints.

The SDK can contain generated OpenAPI wire models, but the CLI must use public
SDK APIs. Do not generate or embed a second transport client in the CLI.

Use a Poetry project with package import name `mammoth_cli`. For local tests,
install the repository SDK and CLI together as editable packages so published
PyPI state cannot mask local SDK changes. Build metadata must contain a normal
version range for `mammoth-io`, not a repository-local file URL.

## Typed SDK boundary

- All Mammoth HTTP calls pass through public `mammoth-io` APIs.
- CLI source must not import `requests`, `httpx`, or another Mammoth transport.
- CLI source must not call a symbol whose name starts with `_`.
- Add missing public SDK methods before adding their commands.
- Generate Pydantic v2 wire models from the pinned OpenAPI snapshot.
- Put ergonomic validation and stable public names in curated SDK request
  models when generated wire names are unsuitable.
- Keep `Any` inside the narrow SDK normalization adapter.
- Run strict mypy on the CLI.

Define a typed `MammothService` protocol. Command tests use a typed fake service.
Production uses one `SdkMammothService` backed by `MammothClient`.

## Command structure

Use singular resource nouns and consistent verbs. The initial command tree must
include all applicable OpenAPI families, including those missing from the
current SDK:

```text
agent, annotation, automation, batch, browse, client-app, connector
dashboard, data-app, dataset, derivative, external-key, file, folder
job, notification, parameter, project, report, schedule, snippet
support, billing, template, trash, user, view, webhook, workflow
```

Nested view groups include:

```text
view data
view task
view pipeline
view draft
view checkpoint
view version
view data-check
view derivative
view conditional-format
view transform
view export
```

Use `list`, `get`, `create`, `update`, and `delete` when those verbs match the
API operation. Use exact domain verbs such as `trash`, `restore`, `rerun`,
`preview`, `apply`, `share`, `duplicate`, `publish`, `wait`, and `upload` where
needed.

Aliases must appear in the parity manifest but must not duplicate handlers.

## Global options

```text
--profile PROFILE
--project PROJECT_ID
--base-url URL
--timeout SECONDS
--job-timeout SECONDS
--pipeline-timeout SECONDS
--output table|json|yaml|ndjson|plain
--color auto|always|never
--no-input
--no-progress
--debug
--version
```

`--base-url` is an expert runtime override. It is not an authentication input.

Interactive login example:

```bash
mammoth auth login --workspace WORKSPACE_ID
```

This command prompts securely for the API key and secret. The default prefix is
`app-eu`. Agents and CI can omit saved login and use the documented environment
variables. Keep the `release` test target out of product help and examples.

## Structured input

- Use typed flags for common scalar values.
- Use repeatable flags for simple lists.
- Use `--input FILE|-` for strict command-specific JSON or YAML.
- Detect file format from the suffix.
- Require `--input-format` for stdin.
- Use `yaml.safe_load`.
- Reject unknown fields.
- Explicit flags override document fields.
- Never read stdin unless the user supplies `-` or a secret-stdin option.
- Never evaluate Python or shell expressions.

Every command request model uses `extra="forbid"`. Generate and publish its JSON
Schema.

## Shared condition model

Use one recursive, discriminated condition model for all condition-bearing
operations:

```yaml
column: Sales
operator: GTE
value: 1000
case_sensitive: null
value_is_column: false
value_is_date_fn: false
component: null
truncate: null
```

Compound examples:

```yaml
and:
  - {column: Sales, operator: GTE, value: 1000}
  - not: {column: Status, operator: EQ, value: Closed}
```

Rules:

- `and` and `or` require at least two nodes.
- A node has exactly one leaf, `and`, `or`, or `not` form.
- Empty-value operators reject a supplied value.
- Other operators require a value.
- `IN_RANGE` requires exactly two values.
- Column and date-function value modes are mutually exclusive.
- Conditions are document-only in version 1. Put `condition` in the command's
  `--input` document. Do not let individual command workers invent condition
  flags. A later release can add shared flags through one reviewed contract.

## Output contract

Send result data to stdout. Send diagnostics, warnings, progress, and errors to
stderr. Never put Rich markup, a spinner, or a banner into machine stdout.

Success:

```json
{
  "schema_version": 1,
  "data": {},
  "meta": {
    "command": "dataset list",
    "profile": "default",
    "workspace_id": 123,
    "project_id": 456,
    "pagination": null
  }
}
```

Failure:

```json
{
  "schema_version": 1,
  "error": {
    "code": "dataset_not_found",
    "message": "The dataset does not exist.",
    "hint": "Check the dataset ID.",
    "details": {},
    "request_id": null,
    "retryable": false,
    "authorization_required": false,
    "recovery_commands": []
  }
}
```

Normalize dictionaries, lists, Pydantic models, dataclasses, enums, paths,
dates, jobs, exports, and `View`. Exclude sessions, clients, and secrets.

Exit statuses:

```text
0   success
1   API or operation failure
2   usage, input, or confirmation failure
4   authentication or authorization failure
5   resource not found
6   conflict or failed precondition
7   retryable network, timeout, or rate-limit failure
130 interruption
```

## Pagination and waiting

Each operation manifest record must state one pagination policy:

- `none`.
- `offset` with the actual result envelope.
- `cursor` with the actual token.
- `single_page` when the SDK or API cannot continue safely.

Offer `--all` only for a proven continuation contract. Never infer completeness
from an undocumented response.

Each asynchronous operation must state one wait policy:

- `always_wait`.
- `start_or_wait`.
- `returns_job`.
- `not_async`.

Do not advertise `--no-wait` until the public SDK can return a stable submitted
job or task result.

## Secret transport

Mark secret fields in typed models. Redact recursively in all outputs and debug
logs. Use destination-specific environment variables, secure prompts, stdin,
or permission-checked files. A command that creates a one-time secret must
require an explicit secure output file or an explicit TTY-only show option.

## Complete bulk-replace command contract

Simple form:

```bash
mammoth --project 42 view transform bulk-replace 1039 \
  --column "Item" \
  --search "6 inch CAKE" \
  --search "8 inch CAKE" \
  --replace "CAKE"
```

Multiple groups:

```bash
mammoth --project 42 view transform bulk-replace 1039 \
  --input replacements.yaml
```

```yaml
columns: [Item]
mapping:
  - search: [6 inch CAKE, 8 inch CAKE]
    replace: CAKE
  - search: [COKE 330ML, Coca Cola Can]
    replace: COKE
match_case: true
match_words: false
condition: null
```

Stdin form:

```bash
mammoth --project 42 view transform bulk-replace 1039 \
  --input - --input-format yaml
```

The positional `VIEW_ID` is a positive integer. Shortcut mode requires one or
more `--column`, one or more `--search`, and exactly one `--replace`. It creates
exactly one mapping group. An empty replacement is valid, so presence—not
truthiness—validates `--replace`.

Document mode accepts the strict `BulkReplaceRequest` shown above. It requires
at least one unique nonempty column, one mapping, and one unique nonempty search
value in each mapping. It rejects unknown fields. `condition` uses the shared
recursive condition model.

Shortcut mapping options and a document `mapping` are mutually exclusive. A
document can be combined only with these explicit scalar overrides:

```text
--column COLUMN...                    replaces the complete document columns
--match-case / --ignore-case          overrides match_case; default true
--match-words / --match-substrings     overrides match_words; default false
```

If any `--search` or `--replace` option is present with `--input`, fail with
exit status `2` and code `invalid_input_mode`. Require `--input-format json|yaml`
for stdin. Detect JSON or YAML from a file suffix otherwise.

Resolve every display column before mutation. Convert each document mapping to
`BulkReplaceMapping`. Call only public
`mammoth.view.View.bulk_replace(columns, mapping, match_case, match_words,
condition)`. Never call an SDK private member or a Mammoth HTTP endpoint.

Bulk replace is a reversible pipeline mutation. It needs no `--yes`. Its v1
wait policy is `always_wait`; do not expose `--no-wait` until the public SDK has
a stable submitted-task result. The result is `PipelineMutationResult` with
`view_id`, `dataset_id`, final pipeline state, draft state, and task identity
when the server returns one. If a task ID exists, human output prints the exact
rollback command `mammoth view task delete VIEW_ID TASK_ID`. Never promise undo
when the server returns no stable task ID.

All view transformations depend on `server_backed_draft_state`. A handler is
not acceptable until draft enter, transform, status, submit, and discard work
across separate processes.

Required bulk-replace tests:

```text
UT-VIEW-BULK-REPLACE
CT-VIEW-BULK-REPLACE-HUMAN
CT-VIEW-BULK-REPLACE-JSON
CT-VIEW-BULK-REPLACE-ERROR
CT-VIEW-BULK-REPLACE-DEFAULTS
CT-VIEW-BULK-REPLACE-INPUT-MODES
LT-VIEW-BULK-REPLACE
LT-VIEW-BULK-REPLACE-DRAFT
LT-VIEW-BULK-REPLACE-UNDO
```

The live test uses known case variants and partial words. It verifies output
data for default case matching, `--ignore-case`, `--match-words`, a recursive
condition, multiple mapping groups, and an empty replacement. It deletes the
task and verifies restored data. The current tenant cannot run this test until
dataset creation or upload permission is granted.
