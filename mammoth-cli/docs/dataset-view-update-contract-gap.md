# Dataset and view update contract gap

`dataset update` and `view update` intentionally reject raw patch input. The
CLI must not infer a backend patch grammar from examples or permissive OpenAPI
fields. This is a safety boundary, not a claim that the API routes do not exist.

For REL-292, `PATCH /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}`
accepts `DatasetPatchRequest`. Its `patch` and `patches` forms mix rename,
column, refresh, connection, and schema-setting effects. The current public SDK
`DatasetsAPI.update` instead sends a list to the plural `/datasets` endpoint,
so it is not a binding for the singular OpenAPI operation. Use the existing
typed `dataset rename` and `dataset file-settings update` commands where they
fit; leave other variants unavailable.

For REL-294, `PATCH /workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}/dataviews/{dataview_id}`
accepts one `DataviewPatchOp`, but its `op`, `path`, and `value` fields are
free-form. The examples mention a rename and reset but do not define allowed
values, postconditions, or recovery behavior. The CLI therefore rejects the
raw SDK pass-through rather than exposing a deceptively benign mutation.

A future typed command needs the API/spec to provide a discriminated
operation union. The union must give exact paths, value schemas, effect class,
confirmation requirements, async/result shape, and readback/recovery rules. The SDK must
then expose a public method for the exact singular dataset endpoint or a
reviewed equivalent. Add focused contract tests and bounded owned-fixture
evidence before changing either matrix row from `Unassessed`.
