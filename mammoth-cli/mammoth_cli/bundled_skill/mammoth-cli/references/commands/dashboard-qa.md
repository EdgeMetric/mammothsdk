# `dashboard-qa` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `dashboard.qa.ask`

Run: `mammoth dashboard qa ask`. Exact input fields: `mammoth schema get dashboard.qa.ask`.

Example: `mammoth dashboard qa ask 123 123 --input '{"body": {"params": {"question": "Summarize revenue by region"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaAskResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: answer. AI answered with kpi block and narrative text; not quota-gated Single invocation only; no error-path or variant coverage.

### `dashboard.qa.comment.create`

Run: `mammoth dashboard qa comment create`. Exact input fields: `mammoth schema get dashboard.qa.comment.create`.

Example: `mammoth dashboard qa comment create 123 123 --input '{"body": {"params": {"body": "sample"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaCommentCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: session. created comment id=1 on session 1 Single invocation only; no error-path or variant coverage.

### `dashboard.qa.comment.delete`

Run: `mammoth dashboard qa comment delete`. Exact input fields: `mammoth schema get dashboard.qa.comment.delete`.

Example: `mammoth dashboard qa comment delete 123 123 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `DashboardQaCommentDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: session. deleted comment 1 from session 1 Single invocation only; no error-path or variant coverage.

### `dashboard.qa.feedback`

Run: `mammoth dashboard qa feedback`. Exact input fields: `mammoth schema get dashboard.qa.feedback`.

Example: `mammoth dashboard qa feedback 123 123 123 --input '{"body": {"params": {"rating": "up"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaFeedbackResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: session. recorded thumbs-up feedback on message id=2 Single invocation only; no error-path or variant coverage.

### `dashboard.qa.session.create`

Run: `mammoth dashboard qa session create`. Exact input fields: `mammoth schema get dashboard.qa.session.create`.

Example: `mammoth dashboard qa session create 123 --input '{"body": {"params": {"title": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaSessionCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: session. created qa session id=1 on D=52 Single invocation only; no error-path or variant coverage.

### `dashboard.qa.session.delete`

Run: `mammoth dashboard qa session delete`. Exact input fields: `mammoth schema get dashboard.qa.session.delete`.

Example: `mammoth dashboard qa session delete 123 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `DashboardQaSessionDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: ok. deleted forked session 2 and original session 1, both ok:true Single invocation only; no error-path or variant coverage.

### `dashboard.qa.session.fork`

Run: `mammoth dashboard qa session fork`. Exact input fields: `mammoth schema get dashboard.qa.session.fork`.

Example: `mammoth dashboard qa session fork 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaSessionForkResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: session. forked session 1 -> new session id=2 with copied messages Single invocation only; no error-path or variant coverage.

### `dashboard.qa.session.get`

Run: `mammoth dashboard qa session get`. Exact input fields: `mammoth schema get dashboard.qa.session.get`.

Example: `mammoth dashboard qa session get 123 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaSessionGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: session. fetched session 1 Single invocation only; no error-path or variant coverage.

### `dashboard.qa.session.list`

Run: `mammoth dashboard qa session list`. Exact input fields: `mammoth schema get dashboard.qa.session.list`.

Example: `mammoth dashboard qa session list 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaSessionListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Published PyPI CLI 1.1.11 / SDK 0.7.1 Q&A session-list read succeeded for retained dashboard 48 with empty mine/shared lists. One dashboard only; not Full. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: mine, shared. 1 own s…

### `dashboard.qa.session.rename`

Run: `mammoth dashboard qa session rename`. Exact input fields: `mammoth schema get dashboard.qa.session.rename`.

Example: `mammoth dashboard qa session rename 123 123 --input '{"body": {"params": {"title": "Revenue report"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaSessionRenameResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: session. renamed session 1 Single invocation only; no error-path or variant coverage.

### `dashboard.qa.session.set-visibility`

Run: `mammoth dashboard qa session set-visibility`. Exact input fields: `mammoth schema get dashboard.qa.session.set-visibility`.

Example: `mammoth dashboard qa session set-visibility 123 123 --input '{"body": {"params": {"visibility": "sample"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaSessionSetVisibilityResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: session. set visibility=shared Single invocation only; no error-path or variant coverage.

### `dashboard.qa.settings.get`

Run: `mammoth dashboard qa settings get`. Exact input fields: `mammoth schema get dashboard.qa.settings.get`.

Example: `mammoth dashboard qa settings get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaSettingsGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Published PyPI CLI 1.1.11 / SDK 0.7.1 Q&A settings read succeeded for retained dashboard 48. One dashboard only; not Full. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: allow_viewer_qa, can_manage, public_link. returned all…

### `dashboard.qa.settings.set`

Run: `mammoth dashboard qa settings set`. Exact input fields: `mammoth schema get dashboard.qa.settings.set`.

Example: `mammoth dashboard qa settings set 123 --input '{"body": {"params": {"allow_viewer_qa": true}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardQaSettingsSetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: allow_viewer_qa, can_manage, public_link. set allow_viewer_qa=true Single invocation only; no error-path or variant coverage.
