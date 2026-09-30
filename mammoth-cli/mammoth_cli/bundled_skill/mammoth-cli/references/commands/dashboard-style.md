# `dashboard-style` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `dashboard.style.custom.create`

Run: `mammoth dashboard style custom create`. Exact input fields: `mammoth schema get dashboard.style.custom.create`.

Example: `mammoth dashboard style custom create --input '{"body": {"params": {"signals": {}}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStyleCustomCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: style. created custom style id=1 with full unredacted colors/font/viz (no tokens field passed) Single invocation only; no error-path or variant coverage.

### `dashboard.style.custom.delete`

Run: `mammoth dashboard style custom delete`. Exact input fields: `mammoth schema get dashboard.style.custom.delete`.

Example: `mammoth dashboard style custom delete resource-123`. Illustrative only: append `--yes` after observing an owned target.

Result: `DashboardStyleCustomDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: ok. deleted custom style 1 Single invocation only; no error-path or variant coverage.

### `dashboard.style.custom.list`

Run: `mammoth dashboard style custom list`. Exact input fields: `mammoth schema get dashboard.style.custom.list`.

Example: `mammoth dashboard style custom list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStyleCustomListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Bounded release read succeeded with pinned CLI 1.1.9 in workspace 4; empty custom-style list observed. No Full claim: no non-empty fixture. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: styles. empty custom styles list Sing…

### `dashboard.style.custom.update`

Run: `mammoth dashboard style custom update`. Exact input fields: `mammoth schema get dashboard.style.custom.update`.

Example: `mammoth dashboard style custom update resource-123 --input '{"body": {"params": {"signals": {}}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStyleCustomUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: style. renamed custom style 1 Single invocation only; no error-path or variant coverage.

### `dashboard.style.default.get`

Run: `mammoth dashboard style default get`. Exact input fields: `mammoth schema get dashboard.style.default.get`.

Example: `mammoth dashboard style default get`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStyleDefaultGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. CLI defect fixed, confirmed: returned a real matched body {"styleId":"stone"} instead of raising ValidationError on an unmatched 2xx. Single invocation only.

### `dashboard.style.default.set`

Run: `mammoth dashboard style default set`. Exact input fields: `mammoth schema get dashboard.style.default.set`.

Example: `mammoth dashboard style default set --input '{"body": {"params": {"styleId": "sample"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStyleDefaultSetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. Set styleId to the exact value read from style default get ("stone"), i.e. a verified no-op restore. Result {"styleId":"stone"}; re-ran style default get afterward and confirmed it still…

### `dashboard.style.derive`

Run: `mammoth dashboard style derive`. Exact input fields: `mammoth schema get dashboard.style.derive`.

Example: `mammoth dashboard style derive --input '{"body": {"params": {"signals": {}}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStyleDeriveResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.14 — dashboard re-verification 2026-09-18: exit 0 on release with CLI 2.0.14. CLI defect fixed, confirmed: returned a full real styleTokens object (colors, font, viz palette, radius, shadow, etc.) with no '***REDACTED***' placeholders anywhere in the body. Single…

### `dashboard.style.extract-brand`

Run: `mammoth dashboard style extract-brand`. Exact input fields: `mammoth schema get dashboard.style.extract-brand`.

Example: `mammoth dashboard style extract-brand --input '{"body": {"params": {"url": "https://example.com/data.csv"}}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStyleExtractBrandResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.12 — Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: screenshot, signals. captured screenshot + extracted brand signals (accents/font/ground/primary), no redaction here Single invocation only; no error-path or variant coverage.

### `dashboard.style.preset.list`

Run: `mammoth dashboard style preset list`. Exact input fields: `mammoth schema get dashboard.style.preset.list`.

Example: `mammoth dashboard style preset list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStylePresetListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.12 — Bounded release read succeeded with pinned CLI 1.1.9 in workspace 4; 10 stock presets returned. No Full claim: custom preset fixture not observed. Also: Dashboard sweep 2026-09-18: exit 0 on release with CLI 2.0.12; result keys: presets. returns built-in styl…

### `dashboard.style.token.list`

Run: `mammoth dashboard style token list`. Exact input fields: `mammoth schema get dashboard.style.token.list`.

Example: `mammoth dashboard style token list resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardStyleTokenListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.11 — Published PyPI CLI 1.1.11 / SDK 0.7.1 read of observed preset stone returned a redacted token payload. Bounded to one preset and redacted semantics; not Full. Dashboard sweep 2026-09-18 on release observed cli_error: HTTP 200 but result is tokens='***REDACTED…
