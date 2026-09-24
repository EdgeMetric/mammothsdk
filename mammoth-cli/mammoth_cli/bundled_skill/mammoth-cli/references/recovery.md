# Error recovery and cleanup

## Recover from an error
Every error envelope may carry `error.recovery_commands`: exact inspection or
correction commands. Read `error.code` and `details.operation_state` first;
these commands are not blanket permission to replay a mutation.

| exit | error.code (examples) | next step |
|---|---|---|
| 4 | not_authenticated, authentication_failed | `mammoth auth login` |
| 2 | keyring_unavailable, keyring_unresponsive | operator runs `mammoth auth login --storage file` (or unlocks the OS keychain) |
| 5 | resource_not_found | re-list to find the correct id |
| 2 | project_required | `mammoth context project use ID` or `--project` |
| 2 | confirmation_required | re-run with `--yes` (and `--confirm TARGET`) |
| 6 | conflict | inspect current remote state and resolve it |
| 7 | `timeout` with a known job | inspect or wait that job; do not replay the mutation |
| 7 | `outcome_unknown` | reconcile exact target/scope before any replay |
| 7 | `retryable_error` on a read | honor `Retry-After`, then retry the read |
| 130 | interrupted | preserve the handle, inspect it, and checkpoint the state |

## Failure modes by message

| What you see | Cause | Next command |
|---|---|---|
| `only select queries allowed` (from `view transform add-sql`) | the table name was unquoted | use `FROM "view:VIEW_ID"` (quoted) or the quoted display name; see recipes/transforms.md "Aggregate or summarise" |
| `table name ... not found` | placeholder table (`__TABLE__`, `data`) | same fix as above |
| `unknown_option` / "'name' is positional argument 1 of 'project create'" or "pass `--input '{"dataset_id": VALUE}'` after the positional arguments" | per-field flags do not exist | follow the hint verbatim; `schema get COMMAND_ID` shows `positionals` vs `accepted_fields` |
| `invalid_condition` (exit 2, `details.accepted` lists operators) | operator not in the accepted set (symbols `=`, `>` are accepted as aliases of EQ/GT; words like `GREATER` are not) | use an operator from references/input.md |
| `resource_not_found` (exit 5) after `view get VIEW_ID` / `view data get VIEW_ID` without a parent | discovery could not find the view in the selected project | pass `--project PROJECT_ID` and the `DATASET_ID` positional from `view list` |
| `{"data": "<unserializable View>"}` from `view get VIEW_ID` | CLI ≤ 2.0.17 only; fixed in 2.0.18 | upgrade, or rerun as `view get VIEW_ID DATASET_ID` |
| `pipeline_reference_error` (exit 1) from a transform or `view task add`, `details.reference_errors[].reason` `type mismatch` / `not available` | the backend stored the task but cannot bind it to that column (find/replace and text operations take TEXT columns, math takes NUMERIC); the view is in `ref_error` and every read of it fails with `4DTVW019` until the task goes | run the printed `view task delete VIEW_ID TASK_ID --yes`, then convert-type the column or pick a transform for its type; CLI ≤ 2.0.24 reported this as success with `has_error: true` |
| `4DTVW019 INVALID_RESPONSE_GENERATED` on every read of a view made with `view create ... "clone_from"` | backend: the clone is never processed (tasks stay `added`) | delete the copy; export the source view's rows, then run the summary in place as the last step; see recipes/end-to-end.md |
| `status: ready` with `status_info.ready` "more than one plausible way to be read" and `view list` empty | all-text CSV; the platform did not process it | `file upload` (2.0.18) reports this as `need_action`; see recipes/need-action.md |
| `need_action` in `file upload` result | the platform needs a parsing decision (e.g. ambiguous dates) | run the `next_command` it returns (`dataset file-settings get ID`), then `dataset file-settings update ID`; see recipes/need-action.md |
| `confirmation_required` (exit 2) | destructive/high-impact command without `--yes` (and `--confirm TARGET` when policy is confirm_target) | re-run with the flag after you have read the target back by id |
| `4DASH012 DASHBOARD_LEGACY_CREATION_RETIRED` (HTTP 409) from `dashboard create` | legacy engine retired | `dashboard create-blank` or `dashboard v3 generate` |
| `4GENR001 ... params.data` (HTTP 400) from `dashboard pdf export` | route needs a browser-rendered payload | not available from the CLI; report it, do not retry with `{"data": {}}` |
| `'destination'` KeyError in a `view export create` job with handler_type csv_file | generic export route is broken for CSV on release | use `view export csv` |
| `timeout` / `outcome_unknown` (exit 7) | the request may have completed | `job get JOB_ID` if you have one, else re-list the resource (`dataset list`, `view task list VIEW_ID DATASET_ID`) before any replay |
| HTTP 502 / connection errors on every command | backend outage | `mammoth doctor`; wait and re-run doctor until it succeeds; do not replay mutations blindly |

Every error envelope from CLI 2.0.18 carries `error.log_ref` `{file, run_id}`;
the file is the JSONL run log (`mammoth log path`, `mammoth log tail --input '{"errors_only": true}'`)
and holds every HTTP request of that run with status and request id — quote
the `run_id` when reporting a backend fault.

## Stop conditions

Do not run the next mutation on any of these; report the state (with
`log_ref.run_id`) and either recover per the tables above or hand off:
- `auth status` is missing or its `endpoint` does not match the intended environment
- `mammoth doctor` fails
- a dataset is still `need_action` after the settings update
- a read-back after a value-changing step shows a uniform column (all 0 / all one value / all null) or a changed row the condition should not have touched
- a join leaves most rows unmatched and the key samples on both sides do not explain it
- exit 7 / `outcome_unknown` not yet reconciled
- `schema get` rejects a field you need
- capabilities.md says not supported, or you hit an observed blocker for the route you were about to use
- any command would delete an id not in your created-ids list
- a secret would have to go in argv

## Cleanup discipline
In a shared project, delete only the resources you created, and never touch
pre-existing ones. Track ids you create and remove them when done:
```bash
mammoth dataset delete "$DS" --project 180 --yes
mammoth folder delete "$F" --project 180 --yes
```

## Discovery when stuck
```bash
mammoth capability get GetProjectCheckpoints
mammoth schema get view.transform.pivot
mammoth doctor
```
