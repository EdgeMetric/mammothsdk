# `dashboard-published` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it (use it normally: confirm writes with the user, check the result afterwards), *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `dashboard.published.canvas`

Run: `mammoth dashboard published canvas`. Exact input fields: `mammoth schema get dashboard.published.canvas`.

Example: `mammoth dashboard published canvas https://example.com/data.csv`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPublishedCanvasResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. Returned the full published canvas object (dataset.dataview_id=45, pages, meta.figures={}, etc.) for our own published dashboard 56/url IuZl5tk5KcEHJWTy4tnhrA. Confirms publishing via da…

### `dashboard.published.data`

Run: `mammoth dashboard published data`. Exact input fields: `mammoth schema get dashboard.published.data`.

Example: `mammoth dashboard published data https://example.com/data.csv --input '{"body": {"params": {"descriptor_ids": ["resource-123"]}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPublishedDataResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: observed blocker — blocked_missing_fixture: Could not publish dashboard 59 to reach a live published state: `dashboard action 59 {action:publish-presentation}` failed twice with HTTP 500 outcome_unkn. Re-check before relying on it.

### `dashboard.published.og-card`

Run: `mammoth dashboard published og-card`. Exact input fields: `mammoth schema get dashboard.published.og-card`.

Example: `mammoth dashboard published og-card https://example.com/data.csv`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPublishedOgCardResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.published.pdf-artifact`

Run: `mammoth dashboard published pdf-artifact`. Exact input fields: `mammoth schema get dashboard.published.pdf-artifact`.

Example: `mammoth dashboard published pdf-artifact https://example.com/data.csv 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPublishedPdfArtifactResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — blocked_missing_fixture: Same as dashboard.pdf-artifact: no real pdf job available; used job 313 (descriptor-data job) as the only real job id in hand and got backend_code 4DASH001. Re-check before relying on it.

### `dashboard.published.pdf.export`

Run: `mammoth dashboard published pdf export`. Exact input fields: `mammoth schema get dashboard.published.pdf.export`.

Example: `mammoth dashboard published pdf export https://example.com/data.csv --input '{"body": {"params": {"data": {}}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPublishedPdfExportResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: observed blocker — backend_error: Got backend_code 4PERM002 PERMISSION_ERROR, "User lacks permission to perform given action" on POST /dashboards/url/IuZl5tk5KcEHJWTy4tnhrA/pdf (403), envelope: {"err. Re-check before relying on it.

### `dashboard.published.share-page`

Run: `mammoth dashboard published share-page`. Exact input fields: `mammoth schema get dashboard.published.share-page`.

Example: `mammoth dashboard published share-page https://example.com/data.csv`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPublishedSharePageResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. Returned a real rendered HTML share page (text/html, 1319 bytes, sha256 given) with correct og:title/og:image/redirect script pointing at the dashboard's own url slug. Minor cosmetic bac…

### `dashboard.published.video-artifact`

Run: `mammoth dashboard published video-artifact`. Exact input fields: `mammoth schema get dashboard.published.video-artifact`.

Example: `mammoth dashboard published video-artifact https://example.com/data.csv`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPublishedVideoArtifactResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.published.video.export`

Run: `mammoth dashboard published video export`. Exact input fields: `mammoth schema get dashboard.published.video.export`.

Example: `mammoth dashboard published video export https://example.com/data.csv`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardPublishedVideoExportResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: observed blocker — backend_error: backend_code 4PERM002 PERMISSION_ERROR, "User lacks permission to perform given action" on POST /dashboards/url/IuZl5tk5KcEHJWTy4tnhrA/video (403). Re-check before relying on it.
