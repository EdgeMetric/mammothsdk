# Exports and artifacts

```bash
mammoth schema find "view export"
mammoth schema get view.export.csv
mammoth view export csv VIEW_ID --project PROJECT_ID
mammoth view export list VIEW_ID DATASET_ID --project PROJECT_ID
```

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
