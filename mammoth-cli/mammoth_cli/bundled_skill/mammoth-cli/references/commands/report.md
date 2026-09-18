# `report` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `report.list`

Run: `mammoth report list`. Exact input fields: `mammoth schema get report.list --output json --no-input`.

Example: `mammoth report list --output json --no-input`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ReportListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: limit, next, offset, reports. Single read only; no fixture variants, error envelopes, or write paths assessed.
