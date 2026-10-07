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
