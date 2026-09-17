# `agent` commands

### `agent.chat`

Run: `mammoth agent chat`. Exact input fields: `mammoth schema get agent.chat --output json --no-input`.

Example: `mammoth agent chat --input '{"message": "Summarize revenue by region", "scope": {"sample_key": "Status"}}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AgentChatResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `agent.session.delete`

Run: `mammoth agent session delete`. Exact input fields: `mammoth schema get agent.session.delete --output json --no-input`.

Example: `mammoth agent session delete resource-123 --output json --no-input`. Illustrative only: append `--yes` after observing an owned target.

Expected success: `AgentSessionDeleteResult` in the standard JSON envelope; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `agent.session.list`

Run: `mammoth agent session list`. Exact input fields: `mammoth schema get agent.session.list --output json --no-input`.

Example: `mammoth agent session list --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AgentSessionListResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `agent.session.messages`

Run: `mammoth agent session messages`. Exact input fields: `mammoth schema get agent.session.messages --output json --no-input`.

Example: `mammoth agent session messages resource-123 --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AgentSessionMessagesResult` in the standard JSON envelope; mutation `read`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.

### `agent.session.set-visibility`

Run: `mammoth agent session set-visibility`. Exact input fields: `mammoth schema get agent.session.set-visibility --output json --no-input`.

Example: `mammoth agent session set-visibility resource-123 --input '{"visibility": "sample"}' --output json --no-input`. Runnable only after resolving schema-required IDs and input from observed reads.

Expected success: `AgentSessionSetVisibilityResult` in the standard JSON envelope; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`. On nonzero exit, inspect the JSON error envelope and its `recovery_commands`; do not guess request fields. See [representative envelopes](../machine-output.md) for concrete success/error shapes.
