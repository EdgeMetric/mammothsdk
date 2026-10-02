# `dashboard-template` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it (use it normally: confirm writes with the user, check the result afterwards), *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `dashboard.template.apply`

Run: `mammoth dashboard template apply`. Exact input fields: `mammoth schema get dashboard.template.apply`.

Example: `mammoth dashboard template apply --input '{"body": {"params": {"source_dashboard_id": 1, "target_dataview_id": 1}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplateApplyResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. Succeeded and created a NEW dashboard (id 57, derived_from 56, url U6WuS1Z2haJj8h96JkcFxw) mapped onto view 45 with fidelity {"blocked":false,"dropped":0,"unmatched_required":[]}. This i…

### `dashboard.template.create`

Run: `mammoth dashboard template create`. Exact input fields: `mammoth schema get dashboard.template.create`.

Example: `mammoth dashboard template create --input '{"body": {"params": {"dashboard_id": 1, "title": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplateCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: observed blocker — backend_error: POST /dashboards/v3/templates HTTP 500 empty body / outcome_unknown, as on 2026-09-18. Re-check before relying on it.

### `dashboard.template.delete`

Run: `mammoth dashboard template delete`. Exact input fields: `mammoth schema get dashboard.template.delete`.

Example: `mammoth dashboard template delete resource-123`. Illustrative only: append `--yes` after observing an owned target.

Result: `DashboardTemplateDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: observed blocker — blocked_missing_fixture: dashboard.template.create never produced an owned template (HTTP 500 both attempts, reconciled as not-committed via template list). Re-check before relying on it.

### `dashboard.template.fit`

Run: `mammoth dashboard template fit`. Exact input fields: `mammoth schema get dashboard.template.fit`.

Example: `mammoth dashboard template fit 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplateFitResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: dataview_id, fits. Single read only; no fixture variants, error envelopes, or write paths assessed. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: d…

### `dashboard.template.get`

Run: `mammoth dashboard template get`. Exact input fields: `mammoth schema get dashboard.template.get`.

Example: `mammoth dashboard template get resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplateGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. CLI defect fixed, confirmed: returned a full matched structured body ({"explore":{...},"self_fit":{"grade":"great",...},"source_dashboard_id":1,"template":{...}}) instead of raising Vali…

### `dashboard.template.list`

Run: `mammoth dashboard template list`. Exact input fields: `mammoth schema get dashboard.template.list`.

Example: `mammoth dashboard template list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplateListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.21 — ergonomics sweep 2026-09-19: exit 0 on release with CLI 2.0.21. Returned the template catalogue (formats, functions, ...). Single invocation only.

### `dashboard.template.preview`

Run: `mammoth dashboard template preview`. Exact input fields: `mammoth schema get dashboard.template.preview`.

Example: `mammoth dashboard template preview --input '{"body": {"params": {"source_dashboard_id": 1, "target_dataview_id": 1}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplatePreviewResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: canvas, fidelity, mapping, meta, plan, specs, target_fields. previewed D=52's canvas retargeted to dataview 47 (life expectancy dataset) Single invocation only; no error-path or varia…

### `dashboard.template.rename`

Run: `mammoth dashboard template rename`. Exact input fields: `mammoth schema get dashboard.template.rename`.

Example: `mammoth dashboard template rename resource-123 --input '{"body": {"params": {"title": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplateRenameResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.template.resolve-mapping`

Run: `mammoth dashboard template resolve-mapping`. Exact input fields: `mammoth schema get dashboard.template.resolve-mapping`.

Example: `mammoth dashboard template resolve-mapping --input '{"body": {"params": {"source_dashboard_id": 1, "target_dataview_id": 1}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplateResolveMappingResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: fidelity, mapping, target_fields. resolved mapping from D=52's current dataview (46, GDP after swap-data) to target dataview 47 (life expectancy) Single invocation only; no error-path…

### `dashboard.template.thumbnail.clear`

Run: `mammoth dashboard template thumbnail clear`. Exact input fields: `mammoth schema get dashboard.template.thumbnail.clear`.

Example: `mammoth dashboard template thumbnail clear resource-123`. Illustrative only: append `--yes` after observing an owned target.

Result: `DashboardTemplateThumbnailClearResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.template.thumbnail.get`

Run: `mammoth dashboard template thumbnail get`. Exact input fields: `mammoth schema get dashboard.template.thumbnail.get`.

Example: `mammoth dashboard template thumbnail get resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplateThumbnailGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.template.thumbnail.set`

Run: `mammoth dashboard template thumbnail set`. Exact input fields: `mammoth schema get dashboard.template.thumbnail.set`.

Example: `mammoth dashboard template thumbnail set resource-123 card.png`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardTemplateThumbnailSetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
