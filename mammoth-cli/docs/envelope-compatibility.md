# Envelope compatibility policy

Agents, the MCP server and embedding hosts parse the CLI's envelopes. This page says what
may change in which release, so a consumer knows what it can rely on.

## What the contract covers

- The success envelope: `schema_version`, `data`, `meta`.
- The error envelope: `schema_version`, `error` (`code`, `message`, `hint`, `details`,
  `retryable`, `authorization_required`, `recovery_commands`, `exit`, `log_ref`).
- Exit codes (the table in `references/machine-output.md`).
- Stable `error.code` values and `details.operation_state`.
- `schema get` records, including `output_schema` where a command declares one.
- `mammoth run` line keys and its JSON Lines output.

Message text (`error.message`, `hint`, human output) is not part of the contract: branch on
codes, never on wording.

## `schema_version`

`schema_version` changes only when a change would break a consumer written against the
previous version. Adding a field doesn't change it. Today it is `1`.

| Change | Release | `schema_version` |
|---|---|---|
| New optional field in `meta`, `error` or `details` | minor | same |
| New `error.code`, new command, new `data` field | minor | same |
| New value in an open set (a `status`, a `kind`) | minor | same |
| A `data` field of a command without `output_schema` changes shape | minor, with a CHANGELOG entry | same |
| A field is deprecated | minor; it stays for at least one major | same |
| A field is removed or renamed, or its type changes | major | +1 |
| An exit code changes meaning, or an `error.code` is removed | major | +1 |
| A declared `output_schema` changes incompatibly | major, or the command stops declaring one first (minor) | +1 |

Consumers must ignore fields they don't know. An absent optional field means the same as
`null`.

## Keeping the previous version

When `schema_version` goes up, the CLI keeps returning the previous version for at least
one more major release:

- `embed.invoke(..., schema_version=N)` returns version `N`.
- A version the CLI cannot return raises `ValueError` rather than being reshaped silently.
- A deprecated field is listed under `### Deprecated` in the CHANGELOG with the release
  that removes it.

## Added in mammoth-cli 3.0 (version 1, no break)

- `meta.run_id`: the invocation id. It is the run log's `run_id`, the journal's `inv`
  (`mammoth history show RUN_ID`) and the `inv` in the request's User-Agent.
- `schema get --full` returns `output_schema`.
- `mammoth run` lines take `name`, `when` and `for_each`.
- `history` commands and the `history_not_found`, `journal_off` and
  `unresolved_reference` error codes.
