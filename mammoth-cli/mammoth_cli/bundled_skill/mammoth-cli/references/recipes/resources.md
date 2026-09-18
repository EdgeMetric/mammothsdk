# Files, URL imports, datasets, views and settings

Uploads and dataset creation return a dataset id, not a view id. Every
pipeline transform, `join`'s `foreign_view`, export, and preview needs a view
id instead. Run `view list DATASET_ID --project PROJECT_ID` to get it. Do not
dig through `dataset get` and its `dependencies` field for a view id; `view
list` is the supported route.

Discover exact contracts, then upload and read back explicit parents. A new
project takes its name as the positional argument:

```bash
mammoth project create 'PROJECT NAME' --output json --no-input
mammoth schema get file.upload --output json --no-input
mammoth file upload ./SOURCE.csv --project PROJECT_ID --output json --no-input
mammoth dataset list --project PROJECT_ID --output json --no-input
mammoth view list DATASET_ID --project PROJECT_ID --output json --no-input
mammoth view get VIEW_ID --project PROJECT_ID --output json --no-input
```

`file upload` takes the local path as its positional argument; there is no
`--source`/`--file` option. Its result carries the status the platform holds
for each created dataset: `ready`, or `need_action` with a `next_command`, in
which case follow [need-action](need-action.md) before looking for a view. `dataset delete` is asynchronous: re-read
`dataset list` (the id disappears once the job completes) before reporting.

Use display names from the exact view schema. For settings, folders and other
families, use `schema find`/`schema get` first, then read back the exact parent
and resource IDs. For example:

```bash
mammoth schema find "dataset settings" --output json --no-input
mammoth schema find "folder" --output json --no-input
mammoth schema get dataset.file-settings.get --output json --no-input
mammoth dataset file-settings get DATASET_ID --output json --no-input
```

For a dataset rename, use the typed `dataset rename DATASET_ID` route and
read back the dataset. For file parsing settings, use the typed
`dataset file-settings update DATASET_ID` contract. Do not send raw
`dataset update` patches: rename, refresh, column, reattach, and deletion
patches are freeform at the pinned SDK boundary and are intentionally blocked.
The singular API update route has no public typed SDK binding for its remaining
variants.

If the release returns a different settings route, use the exact match from
`schema find`; do not guess a command name. Snapshot all pre-existing resource
IDs by type. Mark requested datasets/views as retained deliverables before
creating intermediates; cleanup only IDs returned by this task that are
explicitly authorized as temporary or intermediate. Do not blanket-delete
every ID returned by a list.

The upload response is a standard JSON envelope. Treat its `data` object as
opaque until `schema get file.upload` (or the returned command result) names
the IDs to retain; do not assume that a job and dataset are returned together.
Re-read the returned parent dataset and its views before a transform. URL
import is a dataset creation route, not a file-upload shortcut. Upload
authorization is tenant- and scope-specific: a permission envelope means this
attempt is unauthorized, not that `file.upload` is universally blocked. A
retained owned-fixture upload reached ready and was read back, but its final
cleanup absence was not verified; always verify cleanup for IDs returned by
your own run.

The following URL-import shape is a supported documented path, not a claim
that every freeform creation type or `dataset_spec` variant works:

```bash
mammoth schema get dataset.create --output json --no-input
mammoth dataset create --project PROJECT_ID --input \
  '{"ds_creation_type":"weburl","dataset_spec":{"url":"https://example.org/source.csv"}}' \
  --output json --no-input
```

Use the `data` keys actually returned by that response for the subsequent
`dataset get`/`view list`; a creation envelope without a successful readback is
not sufficient. `dataset.create` waits for its asynchronous work, and retained
live evidence recorded five `weburl` OWID imports returning `ready`; other
freeform variants remain unqualified. If the schema does not accept a URL,
report URL import unsupported; do not silently substitute local processing. A
4/5/7 envelope is a failed or uncertain operation, not a usable dataset.
