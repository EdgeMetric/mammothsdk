# Files, URL imports, datasets, views and settings

Uploads and dataset creation return a dataset id, not a view id. Every
pipeline transform, `join`'s `foreign_view`, export, and preview needs a view
id instead. Run `view list DATASET_ID --project PROJECT_ID` to get it. Do not
dig through `dataset get` and its `dependencies` field for a view id; `view
list` is the supported route.

Discover exact contracts, then upload and read back explicit parents.

## Where uploads land

Unless the task names a project, work in one project of your own and put
every dataset of the task there, so the user's real projects stay clean and
one sweep removes everything. `project ensure` is idempotent get-or-create
by exact name: re-running it (or a second task) returns the same id
(`created: false`) instead of making another project. A one-off task can
still use `project create NAME` for a throwaway project.

```bash
mammoth project ensure 'From Claude'   # -> data.project_id, data.created; now the active project
mammoth project ensure 'From Claude'   # same id again, created: false
```

`ensure` saves its project as the profile's active project (`data.active`),
so later commands need no `--project`; pass `--project` only to address a
different project for one call.

Moving a dataset between projects is not a single API call on release;
re-upload into the target project when the task asks for that. To sweep the
working project when the task says it was temporary, delete it (one id per
call, read back) with `project delete ID --yes --confirm ID`; otherwise delete
only the datasets you created and leave the project for the next task.

```bash
mammoth project ensure 'PROJECT NAME'
mammoth schema get file.upload
mammoth file upload ./SOURCE.csv --project PROJECT_ID
mammoth dataset list --project PROJECT_ID
mammoth view list DATASET_ID --project PROJECT_ID
mammoth view get VIEW_ID --project PROJECT_ID
```

## What `file upload` accepts

`file upload` reads the file from local disk and streams it; nothing passes
through your context, so size costs nothing but time. Two boundaries hold:

- Format, by extension: `csv tsv psv txt xls xlsx xml pdf tiff jpeg jpg png
  heic webp`, or an archive of those (`zip gz bz2 tar 7z`). `.json` is not
  accepted; convert to CSV first. Other extensions fail before any upload.
- Size, at the ingress in front of the API: a 60 MB upload is refused with
  HTTP 413 (`invalid_argument`, "larger than Mammoth accepts") before the API
  sees it; 16 MB is accepted. The exact cap between those was not pinned
  down. Keep one upload well under 16 MB: split a larger file by rows and
  upload the parts, or compress it (a `.zip`/`.gz` of a CSV is accepted and
  expanded server-side).

Scanning and parsing time grows with size; the upload waits up to 300 s by
default (`--job-timeout N` to change it) and, when the command returns
`timeout` with a `job_handle`, poll with the `job get` recovery command it
prints instead of uploading again: a second upload of the same file queues a
second job behind the first, and one stuck scan job holds every later upload
in the workspace (seen on release with jobs 667 and 708). A bare HTTP 500 from this route (`outcome_unknown`, empty body) means
the upload service is degraded; check `job get` for a job first, do not
retry in a loop.

`file upload` takes the local path as its positional argument; there is no
`--source`/`--file` option. A path that does not exist is a usage error
(`Local file not found`) before any request. Its result carries the status the platform holds
for each created dataset: `ready`, or `need_action` with a `next_command`, in
which case follow [need-action](need-action.md) before looking for a view. `dataset delete` is asynchronous: re-read
`dataset list` (the id disappears once the job completes) before reporting.

Use display names from the exact view schema. For settings, folders and other
families, use `schema find`/`schema get` first, then read back the exact parent
and resource IDs. For example:

```bash
mammoth schema find "dataset settings"
mammoth schema find "folder"
mammoth schema get dataset.file-settings.get
mammoth dataset file-settings get DATASET_ID
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
attempt is unauthorized, not that `file.upload` is universally blocked. Always
verify cleanup for IDs returned by your own run.

The following URL-import shape is a supported documented path, not a claim
that every freeform creation type or `dataset_spec` variant works:

```bash
mammoth schema get dataset.create
mammoth dataset create --project PROJECT_ID --input \
  '{"ds_creation_type":"weburl","dataset_spec":{"url":"https://example.org/source.csv"}}' \
 
```

Use the `data` keys actually returned by that response for the subsequent
`dataset get`/`view list`; a creation envelope without a successful readback is
not sufficient. `dataset.create` waits for its asynchronous work; only the
`weburl` creation type is proven, other freeform variants remain unqualified.
If the schema does not accept a URL,
report URL import unsupported; do not silently substitute local processing. A
4/5/7 envelope is a failed or uncertain operation, not a usable dataset.
