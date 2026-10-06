# `token` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it (use it normally: confirm writes with the user, check the result afterwards), *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `token.create`

Run: `mammoth token create`. Exact input fields: `mammoth schema get token.create`.

Example: `mammoth token create 'Revenue report'`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `ClientAppCreateResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `token.list`

Run: `mammoth token list`. Exact input fields: `mammoth schema get token.list`.

Example: `mammoth token list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ClientAppListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `token.revoke`

Run: `mammoth token revoke`. Exact input fields: `mammoth schema get token.revoke`.

Example: `mammoth token revoke sample`. Illustrative only: append `--yes` after observing an owned target.

Result: `ClientAppDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.
