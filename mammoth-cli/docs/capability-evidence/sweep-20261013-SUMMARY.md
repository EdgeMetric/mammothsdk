# Capability evidence refresh, 2026-10-13

CLI 2.2.77, `mammoth-cli` from origin/main `20c5eb14f7e9` (release commit "mammoth-io 0.8.41, mammoth-cli 2.2.77"), installed from that tree into a throwaway venv. Same method as the 2026-09-18 and 2026-09-25 sweeps: the real CLI, one call per command, JSON output, a known-answer read-back for writes and transforms. The earlier fence and `COMMANDS.txt` / `targets.json` were never committed, so the harness is committed instead: [sweep-harness-20261013](sweep-harness-20261013/).

Environments: writes and transforms only on koyal (profile `koyal`, dev box); reads on koyal and, read-only, on prod (profile `default`, workspace 304). Prod was never written.

Important limit: the koyal token is limited to project 25654 (an existing project), so every fixture was created inside it and deleted afterwards. A project created through that token (26849) is not accessible by it, so the `project.*` write commands could not be exercised.

## Counts

| sweep | env | run | passed | failed | not run | blocked (no fixture / env) |
|---|---|---|---|---|---|---|
| [read](read-sweep-20261013/SUMMARY.md) | koyal | 139 | 122 | 17 | 17 | 137 |
| [read](read-sweep-20261013/SUMMARY.md) | prod | 165 | 136 | 29 | 17 | 111 |
| [write](write-sweep-20261013/SUMMARY.md) | koyal | 51 | 46 | 5 | 31 | 1 |
| [transform](transform-sweep-20261013/SUMMARY.md) | koyal | 34 | 32 | 2 | 0 | 0 |

"Passed" is exit 0 with a matching read-back (writes, transforms) or exit 0 (reads). "Failed" is a CLI or backend error, a missing result, or a read-back that did not match. Blocked means the command needs an id, file or state that does not exist in that workspace (for example the koyal workspace has no dashboard, connection, data app or agent run); it is not a pass. Not run: the LLM commands (cost), local credential/config families, and the write commands listed with a reason in the write sweep. The dashboard family (144 commands) is mostly unexercised: koyal has no dashboard, the one prod dashboard (id 4, project 2496) uses the v2 engine that the v3 dashboard commands refuse, and creating one costs money.

## Changes against the previous sweeps

Old defects that now pass (read sweep, prod): `webhook.list`, `client-app.list`, `external-key.list`, `browse.root`, `browse.project`, `template.list`, `dashboard.style.default.get`, `workspace.user.get`, `activity.export`, `view.conditional-format.list`, `view.pipeline.items-all`, `connector.get`, `connector.connection.list`, `connector.ai.session.list`.

Write sweep: changed from a failure to a pass since 09-18/2.0.15: `view.derivative.data`, `view.checkpoint.get`, `view.checkpoint.update`, `view.task.preview`; `view.update` (refused by design on 09-18) now renames a view. Changed from a pass to a failure: `batch.update` (see Found 3). The CLI shape errors of 2.0.14 (`folder.move`, `view.checkpoint.*`, `view.conditional-format.*`, `view.derivative.*`, `view.task.*`, `view.pipeline.edit`) did not recur; `view.draft.command` discard needs `--yes --confirm VIEW_ID`.

Transform sweep: 31 of the 32 transforms of 09-25 still match (`ai` does not, Found 6), plus `update-column` (new, matches) and `first-name` (new, partly wrong, Found 5). `convert-type` still skips same-type columns; `fill-missing` direction semantics unchanged.

## Regressions and changes to look at

- `data-app list` is a 404 on both koyal and prod (`GET /data-apps`); it was `ok` (empty) on 09-18. Server route or CLI path changed; the other `data-app` commands could not be run for lack of an id.
- `dataset file-settings get` returns 500 on both koyal and prod for a REST-connector dataset (it was `ok` on a file dataset in 09-18). Probably fixture-dependent (not a file dataset); not run on a file dataset here.
- Prod `dashboard.*` reads on dashboard 4 now fail with "This dashboard uses a different rendering engine" (fixture is a v2-engine board, 09-18 used a v3 board): a fixture difference, not a regression.
- `dashboard source list` failed once on prod with a retryable error and passed on koyal.

## Found (CLI or backend bugs; not fixed in this change)

1. `project create` through a project-limited token succeeds but returns a project the same token cannot read, change or delete (koyal project 26849 "cli-evidence-sweep-1013" is left behind, empty, and needs an admin to delete). The error hint explains it only afterwards.
2. `view export create` without `run_immediately` fails with `invalid_input_field_type`, "export_spec.run_immediately must be an AddExportSpec": the message names the wrong field. With it, koyal answers 5GENR012 "feature disabled for the user-account combination", so no export route could be exercised here.
3. `batch update`: the CLI accepts only an array of ops with `op` replace or remove, and the backend then answers 4GENR007 "patch: Input should be a valid dictionary or instance of BatchesPatchOperation". No shape was found that both accept (the 2.0.15 re-verify recorded it as ok).
4. `view data-check update` with the `disable` command: HTTP 500, "The request may have committed, but its outcome was not confirmed" (same as 09-18).
5. `view transform first-name` returns an empty value for text with a leading space (" alice smith "); unpadded rows are right.
6. `view transform ai` exits 0 but the pipeline ends in `runtime_error` (koyal) and the new column is empty; the 09-25 run on release filled it.
7. `dataset bulk-delete` of 8 ids exited 0 with `data: null` and deleted 7; the remaining one (the lookup source of another view) needed a second call. A silent partial result.
8. The first pass of the write sweep called `view checkpoint get|update|delete` on checkpoint id 1, which did not exist on that view, and each exited 0 (rows with the note in the write results). A missing id should fail loudly.
9. `file update` on a CSV returns 4FILE010 "Invalid file for updating password/extracting sheets" (expected for a file that is not protected; unchanged from 09-18).

Everything above is a record, not a fix; CLI code and command text are untouched by this change.
