# `agent` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `agent.chat`

Run: `mammoth agent chat`. Exact input fields: `mammoth schema get agent.chat`.

Example: `mammoth agent chat --input '{"message": "Summarize revenue by region", "scope": {"sample_key": "Status"}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentChatResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.session.delete`

Run: `mammoth agent session delete`. Exact input fields: `mammoth schema get agent.session.delete`.

Example: `mammoth agent session delete resource-123`. Illustrative only: append `--yes` after observing an owned target.

Result: `AgentSessionDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.session.list`

Run: `mammoth agent session list`. Exact input fields: `mammoth schema get agent.session.list`.

Example: `mammoth agent session list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentSessionListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.11 — Read-only sweep 2026-09-18: exit 0 on release with CLI 2.0.11; result keys: sessions. Single read only; no fixture variants, error envelopes, or write paths assessed.

### `agent.session.messages`

Run: `mammoth agent session messages`. Exact input fields: `mammoth schema get agent.session.messages`.

Example: `mammoth agent session messages resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentSessionMessagesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.session.set-visibility`

Run: `mammoth agent session set-visibility`. Exact input fields: `mammoth schema get agent.session.set-visibility`.

Example: `mammoth agent session set-visibility resource-123 --input '{"visibility": "sample"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentSessionSetVisibilityResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
