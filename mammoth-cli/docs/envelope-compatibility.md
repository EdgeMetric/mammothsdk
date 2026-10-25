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

## Field review for mammoth-cli 2.3 (ver3)

Every envelope field was reviewed for the ver3 work (#314). None is renamed or dropped, so
the envelope is frozen as `schema_version` 1 rather than a new version, and the release is
a minor one (2.3.0): a host written against 2.2 keeps working unchanged, and `embed.invoke(..., schema_version=1)` pins it.

| Field | Decision | Why |
|---|---|---|
| `schema_version` | keep | The version a consumer branches on. |
| `data` | keep | The command's result; its shape is declared by `output_schema` where a command has one. |
| `meta.command` | keep | The command id, the key for `schema get`. |
| `meta.profile`, `meta.workspace_id`, `meta.project_id` | keep | Which account and scope the call ran in. |
| `meta.pagination` | keep | The page a list returned and how to get the next. |
| `meta.dataset`, `meta.view` | keep | The objects a view command resolved. |
| `meta.opens` | keep | The objects a write made or changed; undo reads `created: true` from it. |
| `meta.next_commands` | keep | Suggested follow-ups; advisory, never required. |
| `meta.update_available` | keep | Optional; absent when there is no newer CLI or the check is off. |
| `meta.exit` | keep | The process exit code, for hosts that don't see the process. |
| `meta.run_id` | added | The invocation id that joins the envelope to the run log, the journal and the server's request log. |
| `error.code`, `error.exit`, `error.retryable` | keep | What a consumer branches on. |
| `error.message`, `error.hint` | keep | Human text; not part of the contract (see above). |
| `error.details`, `error.recovery_commands` | keep | Structured context and the commands that fix the error. |
| `error.authorization_required`, `error.log_ref` | keep | Re-login signal; pointer into the local run log. |
| `mammoth run` lines and summary | keep, extended | Per-step envelopes stay one JSON line each; `name`, `when`, `for_each` and the summary's `partial_lines` and `run_id` are additions. |

## Added in mammoth-cli 2.3 (version 1, no break)

- `meta.run_id`: the invocation id. It is the run log's `run_id`, the journal's `inv`
  (`mammoth history show RUN_ID`) and the `inv` in the request's User-Agent.
- `schema get --full` returns `output_schema`.
- `mammoth run` lines take `name`, `when` and `for_each`.
- `history` commands and the `history_not_found`, `journal_off` and
  `unresolved_reference` error codes.
- `recipe list` and `recipe run`, the `recipe_not_found` and `recipe_input_invalid` error
  codes, and `recipes` in `schema find` and `run_command` in `how`.
- `meta.run_id` on the `mammoth run` summary envelope.
- `history resume` and the `nothing_to_resume` and `resume_outcome_unknown` error codes;
  `partial_lines` in the `recipe run` and `history resume` summaries.
