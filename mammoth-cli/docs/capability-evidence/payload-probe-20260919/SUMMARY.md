# Payload probe 2026-09-19 (CLI 2.0.24 tree, release)

Two derivative routes that earlier sweeps recorded as "HTTP 500 on release",
re-run after reading the apiv2 tracebacks on the release host. Both were
payload faults on the CLI's documented example, not backend defects:

| command | finding |
|---|---|
| `view derivative create` | METRIC `ARGUMENT` must be the internal column name (`column_N`); display names raise `KeyError: 'column'`. Created derivative 6 on view 123. |
| `view derivative data` | body is `{"condition": ..., "limit": null}`; `{"limit": null}` suffices; `{}` is 4GENR007. Returned `RESULT: 60.0`. |

Owned fixture: project 52 ('CLI derivative probe'), dataset 104, view 123;
deleted at the end (202 accepted, absent from `project list`).

Still backend after the same check: `view data-check update` (TypeError in
`DataCheck.validate` after commit with the web app's body), browse 500s,
schedule 5GENR011, `dashboard template create` on a dashboard without bound
columns (a fixture requirement, recorded as a restriction).
