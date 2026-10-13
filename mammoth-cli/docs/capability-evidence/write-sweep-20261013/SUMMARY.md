# CLI write sweep, 2026-10-13 (koyal)

CLI 2.2.77 (mammoth-cli from origin/main 20c5eb14f7), SDK from the same tree, installed into a throwaway venv.

Run by `harness/write_sweep.py` (+ `write_sweep2.py`, `write_sweep3.py`: second pass for commands whose first-pass input was wrong in the harness) against fixtures the sweep created in koyal project 25654 (its token cannot reach any other project): three uploads of `transform-sweep-20260925/fixture.csv` and their views, folders, and one appended batch. Every fixture was deleted afterwards (`dataset.bulk-delete`, `file.bulk-delete`, `folder.bulk-delete`); only the empty project 26849 (see below) remains.

Verdicts: ok / ok_empty = exit 0 and the read-back matched; the other verdicts carry the backend or CLI message. `not_run` is never a pass.

| verdict | count |
|---|---|
| blocked_environment | 1 |
| cli_error | 1 |
| not_run | 31 |
| ok | 42 |
| ok_empty | 4 |
| server_error | 1 |
| validation_error | 3 |
| **total** | 83 |

Old = last known result: 2026-09-18 write sweep, overridden by reverify-215 / reverify-216 where a command was re-run.

| command | old | new | note |
|---|---|---|---|
| `ai.condition.generate` | ok | ok |  |
| `ai.expression.generate` | ok (2.0.15) | not_run | not re-run (cost) |
| `ai.retention.condition` | backend_error | not_run | not re-run (cost) |
| `ai.sql.generate` | backend_error (2.0.15) | not_run | not re-run (cost) |
| `ai.suggestion.list` | backend_error (2.0.15) | not_run | not re-run (cost) |
| `batch.bulk-delete` | ok | ok |  |
| `batch.create` | not_rerun (2.0.16) | cli_error | mapping for appending dataset 88933 into dataset 88934 would corrupt the append: destination column(s) not in  |
| `batch.delete` | ok | ok |  |
| `batch.update` | ok (2.0.15) | validation_error | CLI rejects patch as an object (must be an array) and an array item without op replace|remove; with op/path/va |
| `connector.query.generate` | blocked_missing_fixture (2.0.15) | not_run | not re-run (cost); no connector connection on koyal |
| `connector.query.status` | blocked_missing_fixture | not_run | no connector connection on koyal |
| `dataset.bulk-delete` | ok (2.0.15) | ok_empty | cleanup of the sweep's own fixtures |
| `dataset.bulk-update` | cli_error | not_run | acts on all datasets in the project (project not ours) |
| `dataset.create-from-pdf` | backend_error | not_run | no tabular PDF fixture |
| `dataset.file-settings.undo` | ok (2.0.15) | ok |  |
| `dataset.restore` | ok | ok |  |
| `dataset.trash` | (new) | ok |  |
| `dataset.update` | skipped_out_of_scope | not_run | refused by design (unsupported_contract), as in 09-18 |
| `file.bulk-delete` | ok | ok_empty |  |
| `file.delete` | ok | ok_empty |  |
| `file.update` | backend_error | validation_error | Invalid file for updating password/extracting sheets [4FILE010] |
| `folder.bulk-delete` | ok | ok_empty |  |
| `folder.move` | ok (2.0.15) | ok |  |
| `folder.trash` | ok | ok |  |
| `project.bulk-delete` | ok | not_run | same token limit |
| `project.bulk-update` | ok (2.0.15) | not_run | acts on all projects in the workspace |
| `project.create` | ok | not_run | token is limited to project 25654: a project created through it (26849) is not accessible afterwards, so nothi |
| `project.delete` | ok (2.0.15) | not_run | same token limit; project 26849 stays behind (see SUMMARY, Found) |
| `project.publish-credentials` | ok | not_run | no ODBC publish set up on koyal |
| `project.resource-dependencies` | ok_empty | not_run | read route in the old sweep, no own project |
| `project.resource-dependencies.update` | ok | not_run | would change a shared project's settings |
| `project.sample-flow` | ok | not_run | would add a sample flow to a project that is not ours |
| `project.update` | ok (2.0.15) | not_run | same token limit, and no project of ours to change |
| `project.user.add` | ok (2.0.15) | not_run | would change membership of a shared project |
| `project.user.remove` | blocked_missing_fixture | not_run | would change membership of a shared project |
| `project.user.update` | backend_error | not_run | would change membership of a shared project |
| `trash.add` | ok | ok |  |
| `trash.restore` | ok | ok |  |
| `user.preference.update` | ok (2.0.15) | not_run | changes the shared test user's preferences |
| `view.active-user.mark` | ok | ok |  |
| `view.ai.generate-data` | ok | ok |  |
| `view.ai.generation-info` | backend_error | not_run | backend NOT_IMPLEMENTED in 09-18; not re-run |
| `view.ai.profile` | ok (2.0.15) | not_run | not re-run (cost) |
| `view.bulk-delete` | ok | ok |  |
| `view.checkpoint.create` | ok | ok |  |
| `view.checkpoint.delete` | ok (2.0.15) | ok |  |
| `view.checkpoint.delete` | ok (2.0.15) | no_error_on_missing_id | first pass: checkpoint id 1 does not exist on this view (the create had been refused), yet the call exited 0;  |
| `view.checkpoint.get` | backend_error | ok |  |
| `view.checkpoint.get` | backend_error | no_error_on_missing_id | first pass: checkpoint id 1 does not exist on this view (the create had been refused), yet the call exited 0;  |
| `view.checkpoint.update` | backend_error (2.0.15) | ok |  |
| `view.checkpoint.update` | backend_error (2.0.15) | no_error_on_missing_id | first pass: checkpoint id 1 does not exist on this view (the create had been refused), yet the call exited 0;  |
| `view.conditional-format.create` | ok (2.0.16) | ok |  |
| `view.conditional-format.delete-all` | ok (2.0.16) | ok | with rule_id |
| `view.conditional-format.update` | ok_empty | ok |  |
| `view.data-check.create` | ok | ok |  |
| `view.data-check.delete` | ok (2.0.15) | ok |  |
| `view.data-check.get` | ok | ok |  |
| `view.data-check.update` | backend_error | server_error | The request may have committed, but its outcome was not confirmed. |
| `view.delete` | ok | ok |  |
| `view.derivative.create` | ok | ok |  |
| `view.derivative.data` | backend_error | ok |  |
| `view.derivative.delete` | ok (2.0.15) | ok |  |
| `view.derivative.update` | ok (2.0.15) | ok |  |
| `view.draft.command` | ok | ok | enter |
| `view.draft.command` | ok | ok | discard with --yes --confirm |
| `view.export.create` | cli_error | validation_error | This feature is disabled for the user-account combination, contact support team for further details [5GENR012] |
| `view.export.create` | cli_error | blocked_environment | This feature is disabled for the user-account combination [5GENR012] |
| `view.export.delete` | ok | not_run | no export could be created on koyal |
| `view.export.get` | ok | not_run | no export could be created on koyal |
| `view.export.publish-db` | ok | not_run | external effect, no ODBC target |
| `view.export.publish-db-update` | not_rerun (2.0.16) | not_run | external effect, no ODBC target |
| `view.export.update` | ok | not_run | no export could be created on koyal |
| `view.exportable-config.apply` | cli_error | not_run | needs an exportable config from another view; not built |
| `view.pipeline.edit` | ok (2.0.15) | ok |  |
| `view.pipeline.rerun` | ok_empty | ok |  |
| `view.restore` | ok | ok |  |
| `view.task.add` | (new) | ok |  |
| `view.task.delete` | ok | ok |  |
| `view.task.preview` | backend_error (2.0.16) | ok |  |
| `view.task.update` | ok (2.0.15) | ok |  |
| `view.trash` | ok | ok |  |
| `view.update` | skipped_out_of_scope | ok |  |
| `view.version.apply` | ok | ok |  |
| `view.version.delete` | ok_empty | ok |  |
| `view.version.update` | ok_empty | ok |  |
| `workspace.segment.update` | ok (2.0.15) | not_run | changes workspace segments on a shared dev workspace |
