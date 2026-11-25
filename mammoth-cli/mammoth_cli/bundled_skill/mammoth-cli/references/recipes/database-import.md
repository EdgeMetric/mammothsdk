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

List the connection's tables, then pick one (a `shape` of `other` means the
connection has no table list; `needs_sign_in` means it must be signed in again):

```bash
mammoth connector connection tables CONNECTION_KEY
```

Or draft the SQL with `connector query generate`. Try the SELECT first: it shows
sample rows and saves nothing (no dataset, no data source), so it needs no
`--yes`. The CLI accepts only one SELECT (or WITH ... SELECT); the connection's
database user decides what the database allows, and the sample is limited to
the first rows, so add your own LIMIT for a large table:

```bash
mammoth connector connection query mssql CONNECTION_KEY \
  --input '{"query": "SELECT TOP 5 * FROM dbo.Orders"}'
```

Then import it as a dataset (a write: confirm first). `ds_name`, `table_name`
and `query` are all required; without `schedule_properties` it is one pull now:

```bash
mammoth dataset create --input '{"ds_creation_type": "cloud", "dataset_spec":
  {"connector_key": "mssql", "connection_key": "CONNECTION_KEY", "query_properties":
  {"ds_name": "Orders", "table_name": "Orders", "query": "SELECT * FROM dbo.Orders"}}}'
```

`connector ds-config create` is not the import: it checks or samples a query and
saves nothing.

Report the dataset `name` and id from the result (a taken name gets a suffix;
`note` says so). If the call returns an
error envelope, report that envelope as is and stop; do not retry the create
blindly. A bad host, login, or table shows up as the validation error.
