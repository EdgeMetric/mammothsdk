# `activity` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `activity.export`

Run: `mammoth activity export`. Exact input fields: `mammoth schema get activity.export`.

Example: `mammoth activity export`. Discovery only: this command is fail-closed and must not dispatch a request.

Execution is unavailable for the current contract and returns `unsupported_contract`. Do not infer request fields or retry it; use only a separately typed alternative.

Known restriction: BLOCKED[B19 ACTIVITY_EXPORT_UNTYPED_ASYNC]: format/filters/download response are raw; reserved, not registered.

### `activity.list`

Run: `mammoth activity list`. Exact input fields: `mammoth schema get activity.list`.

Example: `mammoth activity list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ActivityListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.18 — fixture-lifecycle sweep 2026-09-19: exit 0 on release with CLI 2.0.18. Returned activity_logs scoped to project 41 (our own actions), e.g. View category entries. Single invocation only.
