# Exports and artifacts

```bash
mammoth schema find "view export"
mammoth schema get view.export.csv
mammoth view export csv VIEW_ID --project PROJECT_ID --input '{"dataset_id": DATASET_ID, "output_path": "out.csv"}'
mammoth view export list VIEW_ID DATASET_ID --project PROJECT_ID
```

`view export csv` takes one positional (the view); `dataset_id` and
`output_path` go in `--input`. It is a download, not a pipeline step.

If the export or its source dataset/view is requested as a deliverable, mark
both as retained before starting. Wait/reconcile returned jobs. Verify local
artifact headers, rows and hash;
for external destinations use required confirmation and destination readback.
Never put connector secrets in argv. Exit 7 or unknown outcome requires
reconciliation before replay.

Representative successful local export data is typically an envelope with a
returned export/artifact identifier or path under `data`; verify that path is
owned, exists, has the expected schema/row count, and hash it. If the command
returns `job_id`, read it until terminal success before inspecting the artifact.
If `schema get view.export.csv` rejects requested fields, preserve the
structured error and discover another declared export route rather than using
raw HTTP.

## Send a view into another project (parallel send, branch-out)

`view export dataset` writes the view's rows into a Mammoth dataset **as a
pipeline step of the source view**, so the copy is refreshed every time the
source pipeline re-runs; existing tasks and existing exports (for example a
Power BI send) are not touched — it is appended at the end of the pipeline.
`target_project_id` puts the dataset in another project (proven on release:
view 134 in project 58 → dataset 114 in project 57, refreshed 302 → 301 rows
after a filter was added upstream).

```bash
mammoth view export dataset SOURCE_VIEW_ID SOURCE_DATASET_ID --yes \
  --input '{"dataset_name": "Finance feed", "target_project_id": TARGET_PROJECT_ID}'
# -> {"dataset_id": N, "project_id": TARGET_PROJECT_ID, "next": "mammoth view list N --project TARGET_PROJECT_ID"}
mammoth view export list SOURCE_VIEW_ID SOURCE_DATASET_ID     # handler internal_dataset, status executed, TARGET_DS_ID N
```

`target_ds_id` writes into an existing dataset instead of creating one
(`save_as_mode` `REPLACE_IN_DS` or `APPEND_TO_DS`). Read the delivery back in
the target project (`view list N --project P`, `view data get`) before
reporting it. Do not build this with `view export create`: the raw
`internal_dataset` spec needs `USER_ID` and the `export_project` /
`project_id` / `source_project_id` trio, and without them the backend answers
`4GENR007 Validation error` with no detail; the typed command fills them.

## Destination exports that carry a secret

`schema get` lists `secret_fields` for every typed destination export
(`postgres`, `mysql`, `mssql`, `redshift`, `elasticsearch`, `ftp`, `sftp`,
`powerbi`, `tableau`, `azure-blob`, `onedrive`, `sharepoint`, `rest`). When
that list is non-empty the request body is written by the operator to a
`0600` file and passed as `--input FILE`; it is never an inline document and
never appears in argv, the run log, or a checkpoint. The connector command is
`external_effect` with `confirmation: yes_always`, so `--yes` is required.

```bash
mammoth schema get view.export.postgres   # read secret_fields, required fields
# operator writes /private/path/request.json (mode 0600):
# {"host":"db.example","port":5432,"database":"analytics","table":"exports",
#  "username":"agent","password":"…","dataset_id":DATASET_ID}
mammoth view export postgres VIEW_ID DATASET_ID --project PROJECT_ID \
  --input /private/path/request.json --yes
mammoth view export list VIEW_ID DATASET_ID --project PROJECT_ID
```

If the operator has not supplied such a file, stop and ask for it; do not
compose the body yourself from values seen in chat.

## Generic export routes

`view export csv` and the typed destination commands are the proven path. The
generic `view export create` accepts a raw `export_spec`; for `handler_type`
`csv_file` the release job failed with a bare `'destination'` key even when
`target_properties.destination` was set, so do not use it for CSV. `view export
publish-db-update` only rotates credentials: the body is
`{"patch":[{"op":"replace","path":"credentials","value":"postgres"|"bigquery"}]}`.
