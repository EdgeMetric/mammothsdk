# View 46 no-parent resolver regression — published 1.1.11

Date: 2026-09-17. This is read-only evidence from the freshly installed
published `mammoth-cli==1.1.11` / `mammoth-io==0.7.1` environment, using the
protected `expanded-live` profile, workspace 4, project 3. No fixture was
created and no export was executed.

Package provenance:

- CLI wheel SHA-256: `25a811dad8d843731d719f20948ffe7df85dfb16a89f4cea1d8999925b54c962`
- CLI sdist SHA-256: `c5339664d5be43a27cd43c15414c5ef896fb0ae229fd135845aa1f96aa765a7e`
- SDK wheel SHA-256: `41e606f1ce4705917449f6f926936abfb1f6e776b9339a42848370456fa7bf6e`
- CLI/SDK versions: `1.1.11` / `0.7.1`; Python `3.14.4`

Schema discovery confirms `view.get`, `view.preview`, and `view.export.list`
accept an omitted dataset parent (the latter two resolve it through their
typed fallback). `view.export.csv` also exposes optional `dataset_id`, but was
not executed because its contract is a disposable-project verification path.

Observed calls:

- `view get 46` without `dataset_id`: exit 0; resolved `id=46`, `ds_id=29`,
  `row_count=6801`, `column_count=9`, status returned.
- `view preview 46` without `dataset_id`: exit 0; returned 9 columns and 50
  rows.
- `view export list 46` without `dataset_id`: exit 0; returned an empty
  page (`limit=50`, `offset=50`, empty `next`). This proves routing and parent
  resolution, but the unexpected offset is retained as a result caveat.
- `view get 46 28` explicit wrong parent: exit 4, structured
  `authorization_required`, HTTP 403, endpoint containing
  `/datasets/28/dataviews/46/pipeline/items`. This is a deterministic
  invalid-parent control, not an authorization boundary for the correct
  parent.

Sanitized output and schema summary hashes are recorded in `RESULTS.json`.
The evidence supports bounded read-path proposals only; it does not support
Full status or export success.
