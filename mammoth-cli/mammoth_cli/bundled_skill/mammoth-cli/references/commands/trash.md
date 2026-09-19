# `trash` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `trash.add`

Run: `mammoth trash add`. Exact input fields: `mammoth schema get trash.add`.

Example: `mammoth trash add --input '{"items": [{"sample_key": "Status"}]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `TrashAddResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Trashed dataset 52 (our sample-flow dataset) directly via trash add without a prior dataset-trash call -> {failed:[],succeeded:[{id:52,name:"Sample data - amazon",type:dataset}]}. Restored again after…

### `trash.list`

Run: `mammoth trash list`. Exact input fields: `mammoth schema get trash.list`.

Example: `mammoth trash list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `TrashListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.9 — Bounded release read succeeded with pinned CLI 1.1.9 in expanded-live; empty trash inventory observed (zero datasets, dataviews, dashboards, automations). No Full claim: no trashed fixture.

### `trash.restore`

Run: `mammoth trash restore`. Exact input fields: `mammoth schema get trash.restore`.

Example: `mammoth trash restore --input '{"items": [{"sample_key": "Status"}]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `TrashRestoreResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.14 — write sweep 2026-09-18: exit 0 on release with CLI 2.0.14. Trashed dataset 51 via dataset trash first (job 325). trash restore with items:[{id:51,type:dataset}] -> {failed:[],succeeded:[{id:51,name:stores.csv 3,type:dataset}]}. Confirmed dataset 51 reappears…
