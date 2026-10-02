# Import a table from a database

"Connect SQL Server (or MySQL, Postgres, ...) and make a dataset from a table"
is a connector flow, not a file upload. Do it with the commands below; never
send the user to the web app only because a command is untried (see
[capabilities](../capabilities.md)).

```bash
mammoth connector list                                    # find the key, e.g. mssql, mysql, postgres
mammoth connector get mssql                               # its spec = the fields a connection needs
mammoth connector connection list mssql                   # reuse an existing connection if one fits
```

Every connector command runs in a project: pass `--project PROJECT_ID` (the
project the dataset should land in) unless one is already set.

No connection yet: ask the user once for every required field from the spec
(host, port, database, username, password, ...). Write them under `config` in a
file with mode 0600, never inline -- `{"config": {"host": "...", "port": 1433,
...}}` -- then create it (a write: get the user's confirmation):

```bash
mammoth connector connection create mssql --input /private/path/request.json --yes
mammoth connector connection get mssql CONNECTION_KEY     # read it back; config is redacted
```

There is no table-browse command. Ask the user for the table (and schema), or
draft the SQL with `connector query generate`. Then import it as a dataset
(a write: confirm first). `query` is required; `validate` is on by default:

```bash
mammoth connector ds-config create mssql CONNECTION_KEY \
  --input '{"query": "SELECT * FROM dbo.Orders", "table": "Orders"}' --yes
mammoth connector ds-config list mssql CONNECTION_KEY
mammoth dataset list --project PROJECT_ID                 # the new dataset must appear
```

Report the dataset name and id. If it does not appear, or the call returns an
error envelope, report that envelope as is and stop; do not retry the create
blindly. A bad host, login, or table shows up as the validation error.
