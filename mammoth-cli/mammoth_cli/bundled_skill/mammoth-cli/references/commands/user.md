# `user` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `user.avatar.delete`

Run: `mammoth user avatar delete`. Exact input fields: `mammoth schema get user.avatar.delete`.

Example: `mammoth user avatar delete`. Illustrative only: append `--yes` after observing an owned target.

Result: `UserAvatarDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `user.avatar.upload`

Run: `mammoth user avatar upload`. Exact input fields: `mammoth schema get user.avatar.upload`.

Example: `mammoth user avatar upload ./sales.csv`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `UserAvatarUploadResult`; mutation `benign_mutation`, confirmation `none`, wait policy `always_wait`.

Status on release: untried; no live run recorded.

### `user.change-password`

Run: `mammoth user change-password`. Exact input fields: `mammoth schema get user.change-password`.

Example: `mammoth user change-password --input /private/path/request.json`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Secret fields: pass the body as `--input FILE` (mode 0600); never inline.

Result: `UserChangePasswordResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `user.delete-account`

Run: `mammoth user delete-account`. Exact input fields: `mammoth schema get user.delete-account`.

Example: `mammoth user delete-account`. Illustrative only: append `--yes --confirm <EXACT_TARGET>` after observing the target.

Result: `UserDeleteAccountResult`; mutation `high_impact`, confirmation `confirm_target`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `user.get`

Run: `mammoth user get`. Exact input fields: `mammoth schema get user.get`.

Example: `mammoth user get`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `UserGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Returned current user's profile (<api user>). Single invocation only.

### `user.preference.get`

Run: `mammoth user preference get`. Exact input fields: `mammoth schema get user.preference.get`.

Example: `mammoth user preference get`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `UserPreferenceGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 1.1.10 — Bounded release read with published CLI 1.1.10 succeeded for user preferences; GLOBAL and WORKSPACE_PREFERENCES returned empty objects. No Full claim: no preference mutation/readback variant.

### `user.preference.update`

Run: `mammoth user preference update`. Exact input fields: `mammoth schema get user.preference.update`.

Example: `mammoth user preference update --input '{"patch": [{"op": "replace", "path": "GLOBAL.PREFERENCES.TOP_TABS", "value": []}]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `UserPreferenceUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.15 — re-verification 2026-09-18: exit 0 on release with CLI 2.0.15. Fix held: command accepted the release {patch:[...]} list shape. Read `user preference get` first (GLOBAL.FIRST_TIME_ON_DL=true), wrote back the SAME value. Response: {"data":{"response":null,"sta…

### `user.update`

Run: `mammoth user update`. Exact input fields: `mammoth schema get user.update`.

Example: `mammoth user update`. Discovery only: this command is fail-closed and must not dispatch a request.

Execution is unavailable for the current contract and returns `unsupported_contract`. Do not infer request fields or retry it; use only a separately typed alternative.

Known restriction: BLOCKED[B17 VARIADIC_INPUT_UNTYPED]: **fields is unconstrained; reserved, not registered.
