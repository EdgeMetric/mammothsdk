# `addon` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `addon.connector.add`

Run: `mammoth addon connector add`. Exact input fields: `mammoth schema get addon.connector.add`.

Example: `mammoth addon connector add --input '{"connector_id": 42}'`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `AddonConnectorAddResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `addon.connector.remove`

Run: `mammoth addon connector remove`. Exact input fields: `mammoth schema get addon.connector.remove`.

Example: `mammoth addon connector remove --input '{"connector_id": 42}'`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `AddonConnectorRemoveResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `addon.list`

Run: `mammoth addon list`. Exact input fields: `mammoth schema get addon.list`.

Example: `mammoth addon list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AddonListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `addon.storage.add`

Run: `mammoth addon storage add`. Exact input fields: `mammoth schema get addon.storage.add`.

Example: `mammoth addon storage add --input '{"additional_storage_gb": 1}'`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `AddonStorageAddResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `addon.storage.remove`

Run: `mammoth addon storage remove`. Exact input fields: `mammoth schema get addon.storage.remove`.

Example: `mammoth addon storage remove --input '{"removal_storage_gb": 1}'`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `AddonStorageRemoveResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `addon.user.add`

Run: `mammoth addon user add`. Exact input fields: `mammoth schema get addon.user.add`.

Example: `mammoth addon user add`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `AddonUserAddResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `addon.user.remove`

Run: `mammoth addon user remove`. Exact input fields: `mammoth schema get addon.user.remove`.

Example: `mammoth addon user remove --input '{"user_count": 1}'`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `AddonUserRemoveResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.
