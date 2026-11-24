# `dashboard-context` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it (use it normally: confirm writes with the user, check the result afterwards), *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `dashboard.context.apply`

Run: `mammoth dashboard context apply`. Exact input fields: `mammoth schema get dashboard.context.apply`.

Example: `mammoth dashboard context apply 123 resource-123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `DashboardContextApplyResult`; mutation `benign_mutation`, confirmation `confirm_target`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `dashboard.context.create`

Run: `mammoth dashboard context create`. Exact input fields: `mammoth schema get dashboard.context.create`.

Example: `mammoth dashboard context create --input '{"body": {"params": {"name": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardContextCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: context. created context id=1 Single invocation only; no error-path or variant coverage.

### `dashboard.context.delete`

Run: `mammoth dashboard context delete`. Exact input fields: `mammoth schema get dashboard.context.delete`.

Example: `mammoth dashboard context delete resource-123 --yes`. Illustrative only: append `--yes` after observing an owned target.

Result: `DashboardContextDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: ok. deleted context 1 Single invocation only; no error-path or variant coverage.

### `dashboard.context.extract`

Run: `mammoth dashboard context extract`. Exact input fields: `mammoth schema get dashboard.context.extract`.

Example: `mammoth dashboard context extract --input '{"body": {"params": {"name": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ContextExtractResponse`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: condensed, figureHeavy, file, rejected, shape, skipped, suggestions. extracted suggestions from raw text Single invocation only; no error-path or variant coverage.

### `dashboard.context.list`

Run: `mammoth dashboard context list`. Exact input fields: `mammoth schema get dashboard.context.list`.

Example: `mammoth dashboard context list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardContextListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Bounded release read succeeded with pinned CLI 1.1.9 in workspace 4; empty context list observed. No Full claim: no non-empty fixture. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: contexts. empty contexts list Single invoc…

### `dashboard.context.review`

Run: `mammoth dashboard context review`. Exact input fields: `mammoth schema get dashboard.context.review`.

Example: `mammoth dashboard context review 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardContextReviewResult`; mutation `read`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `dashboard.context.update`

Run: `mammoth dashboard context update`. Exact input fields: `mammoth schema get dashboard.context.update`.

Example: `mammoth dashboard context update resource-123 --input '{"body": {"params": {"name": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardContextUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: context. renamed context 1 Single invocation only; no error-path or variant coverage.
