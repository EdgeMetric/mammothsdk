# `dashboard-embed` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it (use it normally: confirm writes with the user, check the result afterwards), *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `dashboard.embed.config.get`

Run: `mammoth dashboard embed config get`. Exact input fields: `mammoth schema get dashboard.embed.config.get`.

Example: `mammoth dashboard embed config get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardEmbedConfigGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.embed.config.set`

Run: `mammoth dashboard embed config set`. Exact input fields: `mammoth schema get dashboard.embed.config.set`.

Example: `mammoth dashboard embed config set 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `DashboardEmbedConfigSetResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.embed.key.rotate`

Run: `mammoth dashboard embed key rotate`. Exact input fields: `mammoth schema get dashboard.embed.key.rotate`.

Example: `mammoth dashboard embed key rotate 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `DashboardEmbedKeyRotateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.embed.lifetime.set`

Run: `mammoth dashboard embed lifetime set`. Exact input fields: `mammoth schema get dashboard.embed.lifetime.set`.

Example: `mammoth dashboard embed lifetime set 123 --input '{"token_ttl": 1}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardEmbedLifetimeSetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.embed.origin.revoke`

Run: `mammoth dashboard embed origin revoke`. Exact input fields: `mammoth schema get dashboard.embed.origin.revoke`.

Example: `mammoth dashboard embed origin revoke 123 --input '{"origin": "https://example.com"}' --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `DashboardEmbedOriginRevokeResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.embed.preview-token.create`

Run: `mammoth dashboard embed preview-token create`. Exact input fields: `mammoth schema get dashboard.embed.preview-token.create`.

Example: `mammoth dashboard embed preview-token create 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardEmbedPreviewTokenCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.embed.secret.rotate`

Run: `mammoth dashboard embed secret rotate`. Exact input fields: `mammoth schema get dashboard.embed.secret.rotate`.

Example: `mammoth dashboard embed secret rotate 123 --yes --confirm 123`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `DashboardEmbedSecretRotateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.embed.usage.get`

Run: `mammoth dashboard embed usage get`. Exact input fields: `mammoth schema get dashboard.embed.usage.get`.

Example: `mammoth dashboard embed usage get 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardEmbedUsageGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `dashboard.embed.usage.summary`

Run: `mammoth dashboard embed usage summary`. Exact input fields: `mammoth schema get dashboard.embed.usage.summary`.

Example: `mammoth dashboard embed usage summary --input '{"dashboard_ids": [1]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `DashboardEmbedUsageSummaryResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
