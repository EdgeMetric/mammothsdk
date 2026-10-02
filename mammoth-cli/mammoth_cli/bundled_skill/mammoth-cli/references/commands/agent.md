# `agent` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it (use it normally: confirm writes with the user, check the result afterwards), *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `agent.action.delete`

Run: `mammoth agent action delete`. Exact input fields: `mammoth schema get agent.action.delete`.

Example: `mammoth agent action delete resource-123`. Illustrative only: append `--yes` after observing an owned target.

Result: `AgentActionDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.action.list`

Run: `mammoth agent action list`. Exact input fields: `mammoth schema get agent.action.list`.

Example: `mammoth agent action list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentActionListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.chat`

Run: `mammoth agent chat`. Exact input fields: `mammoth schema get agent.chat`.

Example: `mammoth agent chat --input '{"message": "Summarize revenue by region", "scope": {"sample_key": "Status"}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentChatResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.run.extend`

Run: `mammoth agent run extend`. Exact input fields: `mammoth schema get agent.run.extend`.

Example: `mammoth agent run extend resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentRunExtendResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.run.list`

Run: `mammoth agent run list`. Exact input fields: `mammoth schema get agent.run.list`.

Example: `mammoth agent run list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentRunListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.run.pause`

Run: `mammoth agent run pause`. Exact input fields: `mammoth schema get agent.run.pause`.

Example: `mammoth agent run pause resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentRunPauseResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.run.resume`

Run: `mammoth agent run resume`. Exact input fields: `mammoth schema get agent.run.resume`.

Example: `mammoth agent run resume resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentRunResumeResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.run.status`

Run: `mammoth agent run status`. Exact input fields: `mammoth schema get agent.run.status`.

Example: `mammoth agent run status`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentRunStatusResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.run.stop`

Run: `mammoth agent run stop`. Exact input fields: `mammoth schema get agent.run.stop`.

Example: `mammoth agent run stop resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentRunStopResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.run.units.set`

Run: `mammoth agent run units set`. Exact input fields: `mammoth schema get agent.run.units.set`.

Example: `mammoth agent run units set resource-123 --input '{"step": 1, "kind": "sample", "units": [{"sample_key": "Status"}]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentRunUnitsSetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

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
