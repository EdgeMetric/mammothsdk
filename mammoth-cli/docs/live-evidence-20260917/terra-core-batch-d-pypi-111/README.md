# Core mutation batch D — owned disposable fixture

Scope: workspace 4 / project 3 with the approved `expanded-live` profile. The
client was an isolated installation from the public PyPI `mammoth-cli` 1.1.11
wheel (SHA-256 `25a811dad8d843731d719f20948ffe7df85dfb16a89f4cea1d8999925b54c962`)
and `mammoth-io` 0.7.1. No retained dataset (28, 29, 30, 31, or 33), view 46,
or dashboard 48 was mutated.

## Owned lifecycle

The schema-documented `dataset.create` web-url path created one disposable
dataset, returned dataset 35 and job 160, and completed successfully. Readback
observed its default view 50 under exact parent 35. The following successful
`view.create` call returned owned view 51 under parent 35. Its response hash is
`2e44b836c6579402e69f957271d5383792e60a77e28eb38f6eaa1a002a64c0aa`.

Sanitized mutation argv (each also used `--output json --no-input --profile
expanded-live --project 3`) were: `dataset create` with the schema-documented
web URL input, `view create 35 --input {"name":"Batch D disposable view"}`,
`dataset file-settings update 35` with the four baseline parsing fields, and
`dataset delete 35 --yes`. Dataset 35, views 50/51, and jobs 160/162/163 are
returned nonsecret identifiers only.

The dataset file-settings baseline was comma delimiter, header enabled, zero
initial skipped rows, and double-quote quote character. `dataset
file-settings update` was invoked with exactly that baseline—no parsing change
was introduced—and returned job 162 (response hash
`ca9058402158c3632a89370cf0e11815b62cb45a1ce84888a2870baabe715692`).
The settings readback matched the baseline and the view readback confirmed both
owned views 50 and 51 have parent dataset 35.

`dataset.update` and `view.update` were not sent. Their exact schemas mark
their `patch_data` contracts as untyped/blocked (`B07` and `B09`), so a patch
was neither invented nor inferred.

Cleanup used only returned dataset 35: `dataset delete 35 --yes` returned job
163 (response hash
`c26118b4d8434a7c200e5dfb17bae5f17be35831b9699319ee0268fb96ca3e98c`).
The subsequent scoped dataset list succeeded and no longer contained 35
(response hash
`c01fb96505c7a23490b57758dbb287bac5e12932fc3296886e800750fd81d98c`).
A direct post-delete get returned structured 403, which is recorded in
`dataset-35-post-delete.json` and is not used as absence proof. Retained
dataset 29 was independently read successfully after cleanup in
`retained-dataset-29-postcheck.json`.

The two JSON captures contain UTC timestamp, sanitized argv, exit code and raw
envelope hashes, with structural response summaries only. This README records
the remaining mutation hashes without raw responses, secrets, or source data.

## Matrix proposals (not applied)

| Row | Proposal | Rationale |
|---|---|---|
| REL-446 `view.create` | Partial | One returned owned view 51 was created under returned parent dataset 35 and read back before verified cleanup. One fixture and lifecycle only; not Full. |
| REL-467 `dataset.file-settings.update` | Partial | Typed required baseline fields were sent on owned dataset 35 and an identical remote settings readback followed. This verifies a safe no-op update path only; not Full. |
| REL-292 `dataset.update` | Unassessed | Schema blocks its arbitrary patch-data contract; no mutation dispatched. |
| REL-294 `view.update` | Unassessed | Schema blocks its arbitrary patch-data contract; no mutation dispatched. |
