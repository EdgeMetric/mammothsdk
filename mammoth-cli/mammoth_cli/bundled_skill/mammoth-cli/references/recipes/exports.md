# Exports and artifacts

```bash
mammoth schema find "view export" --output json --no-input
mammoth schema get view.export.csv --output json --no-input
mammoth view export csv VIEW_ID --project PROJECT_ID --output json --no-input
mammoth view export list VIEW_ID DATASET_ID --project PROJECT_ID --output json --no-input
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

## Generic export routes

`view export csv` and the typed destination commands are the proven path. The
generic `view export create` accepts a raw `export_spec`; for `handler_type`
`csv_file` the release job failed with a bare `'destination'` key even when
`target_properties.destination` was set, so do not use it for CSV. `view export
publish-db-update` only rotates credentials: the body is
`{"patch":[{"op":"replace","path":"credentials","value":"postgres"|"bigquery"}]}`.
