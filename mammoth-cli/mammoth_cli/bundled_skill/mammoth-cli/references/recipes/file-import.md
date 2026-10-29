# Import a file from an SFTP server

"Import import.csv from my SFTP server as a new dataset" is a connector flow,
not a file upload and not an export: Mammoth can read files from SFTP (and
Google Drive, Dropbox, S3-style buckets) through a connection. Do it with the
commands below; never send the user to the upload card because a command is
untried (see [capabilities](../capabilities.md)). `view export sftp` pushes data
OUT to a server; it is not this.

Every connector command runs in a project: pass `--project PROJECT_ID` (the
project the dataset should land in) unless one is already set.

```bash
mammoth connector connection list sftp                    # reuse a connection to this host if one exists
mammoth connector get sftp                                # its spec = the fields a connection needs
```

No connection yet: ask the user once for the host, port, username and password
(`mammoth connector get sftp` lists no fields; the SFTP ones are `domain` (the host
name), `port`, `username`, `password`). Write them under `config` in a file with mode 0600, never inline --
`{"config": {"domain": "sftp.example.com", "port": 22, "username": "...",
"password": "..."}}` -- then create it (a write: get the user's
confirmation):

```bash
mammoth connector connection create sftp --input /private/path/request.json --yes
mammoth connector connection get sftp CONNECTION_KEY      # read it back; config is redacted
```

Then import the file as a dataset (a write: confirm first). `file_path` is the
path on the server, for example the one the user gave; `ds_name` is the new
dataset's name. The command waits for the import and returns the dataset id:

```bash
mammoth dataset create --yes --input '{"ds_creation_type": "cloud", "dataset_spec": {
  "connector_key": "sftp", "connection_key": "CONNECTION_KEY",
  "query_properties": {"ds_name": "import", "file_path": "/data/import.csv"}}}'
mammoth view list DATASET_ID                              # the new dataset must have a view
```

Report the dataset name and id. If the call returns an error envelope (a bad
host, login or path shows up here), report it as is and stop; do not retry the
create blindly.

## Replace instead of add

An upload into an existing dataset adds its rows by default. To replace them
instead, set the dataset's update method once; every later upload then replaces:

```bash
mammoth dataset update-method get DATASET_ID              # the current mode: add or replace
mammoth dataset update-method set DATASET_ID --input '{"mode": "replace"}'
mammoth file upload ./new.csv --input '{"append_to_ds_id": DATASET_ID}'
```

Set it back with `{"mode": "add"}` before the next upload if the rows should be
added again. The setting stays on the dataset, not on one file.

If the file's columns do not match the dataset's, `file upload` exits 1 with
`schema_mismatch` (`rows_added` 0, `kept_dataset_ids`, a next step): nothing was
added and the file's own dataset stays in the project. Fix the columns or the
dataset's `schema_mapping` (`dataset update-method set`); `override_target_schema`
is allowed only under `replace`, with `append_to_ds_id` and the wait.

## Undo an append

To take back the rows one upload added, list the dataset's batches and delete
the one to remove. Deleting a batch removes its rows (a write: confirm first):

```bash
mammoth batch list DATASET_ID                             # each batch: its id and row count
mammoth batch delete DATASET_ID BATCH_ID --yes
```

`mammoth history undo` also reverts an append. Use `batch list` and
`batch delete` when the batch is not the last change.
