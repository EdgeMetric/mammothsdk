# Cross-project send 2026-09-19 (release, projects 57/58)

The ILG feasibility review's first blocker — "a parallel send from a source
project's pipeline into a new project has no proven CLI route" — is closed.

| step | result |
|---|---|
| upload `f_schoolpnl.csv` (synthetic, 302 rows) into project 58 | dataset 112 (`need_action` on an ambiguous date → `file-settings update date_format US`), view 134 |
| raw `view export create` internal_dataset with the web app's cross-project properties | 4GENR007 without `USER_ID`; with `USER_ID` → job 831, dataset 113 in project 57 (302 rows) |
| add a filter on view 134 | source 301 rows; dataset 113's view re-materialised at 301 rows → the send is a pipeline step, refreshed on every run |
| typed `view export dataset ... target_project_id 57` (SDK 0.7.13) | dataset 114 in project 57; result names dataset, project and the next read |

What the SDK/CLI now do for the caller: read the user id once (`/self`), set
`USER_ID`, `export_project`, `project_id`, `source_project_id`; append with
`end_of_pipeline: true` so no existing task or export moves.

Owned fixture: projects 57 ('ILG sim target') and 58 ('ILG sim source A');
kept for the ILG simulation run that follows, deleted at its end.
