# `agent` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it (use it normally: confirm writes with the user, check the result afterwards), *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `agent.access.set`

Run: `mammoth agent access set`. Exact input fields: `mammoth schema get agent.access.set`.

Example: `mammoth agent access set sample --input '{"role": "member", "propose": true}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentAccessSetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

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

### `agent.charter.get`

Run: `mammoth agent charter get`. Exact input fields: `mammoth schema get agent.charter.get`.

Example: `mammoth agent charter get sample`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentCharterGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.charter.restore`

Run: `mammoth agent charter restore`. Exact input fields: `mammoth schema get agent.charter.restore`.

Example: `mammoth agent charter restore sample 123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentCharterRestoreResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.charter.set`

Run: `mammoth agent charter set`. Exact input fields: `mammoth schema get agent.charter.set`.

Example: `mammoth agent charter set sample --input '{"charter": "Watch weekly margin and report the three biggest drops."}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentCharterSetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.charter.versions`

Run: `mammoth agent charter versions`. Exact input fields: `mammoth schema get agent.charter.versions`.

Example: `mammoth agent charter versions sample`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentCharterVersionsResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.chat`

Run: `mammoth agent chat`. Exact input fields: `mammoth schema get agent.chat`.

Example: `mammoth agent chat --input '{"message": "Summarize revenue by region", "scope": {"sample_key": "Status"}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentChatResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.create`

Run: `mammoth agent create`. Exact input fields: `mammoth schema get agent.create`.

Example: `mammoth agent create Status --input '{"name": "Revenue report"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentCreateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.delete`

Run: `mammoth agent delete`. Exact input fields: `mammoth schema get agent.delete`.

Example: `mammoth agent delete sample`. Illustrative only: append `--yes` after observing an owned target.

Result: `AgentDeleteResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.disable`

Run: `mammoth agent disable`. Exact input fields: `mammoth schema get agent.disable`.

Example: `mammoth agent disable sample`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentDisableResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.feedback.list`

Run: `mammoth agent feedback list`. Exact input fields: `mammoth schema get agent.feedback.list`.

Example: `mammoth agent feedback list sample`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentFeedbackListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.get`

Run: `mammoth agent get`. Exact input fields: `mammoth schema get agent.get`.

Example: `mammoth agent get sample`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.goldens.add`

Run: `mammoth agent goldens add`. Exact input fields: `mammoth schema get agent.goldens.add`.

Example: `mammoth agent goldens add sample --input '{"question": "Summarize revenue by region", "expected": "sample"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentGoldensAddResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.goldens.list`

Run: `mammoth agent goldens list`. Exact input fields: `mammoth schema get agent.goldens.list`.

Example: `mammoth agent goldens list sample`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentGoldensListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.goldens.remove`

Run: `mammoth agent goldens remove`. Exact input fields: `mammoth schema get agent.goldens.remove`.

Example: `mammoth agent goldens remove sample 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `AgentGoldensRemoveResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.goldens.run`

Run: `mammoth agent goldens run`. Exact input fields: `mammoth schema get agent.goldens.run`.

Example: `mammoth agent goldens run sample`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentGoldensRunResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.goldens.status`

Run: `mammoth agent goldens status`. Exact input fields: `mammoth schema get agent.goldens.status`.

Example: `mammoth agent goldens status sample`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentGoldensStatusResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.list`

Run: `mammoth agent list`. Exact input fields: `mammoth schema get agent.list`.

Example: `mammoth agent list`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.memory.add`

Run: `mammoth agent memory add`. Exact input fields: `mammoth schema get agent.memory.add`.

Example: `mammoth agent memory add sample --input '{"name": "Revenue report", "content": "sample"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentMemoryAddResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.memory.list`

Run: `mammoth agent memory list`. Exact input fields: `mammoth schema get agent.memory.list`.

Example: `mammoth agent memory list sample`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentMemoryListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.memory.remove`

Run: `mammoth agent memory remove`. Exact input fields: `mammoth schema get agent.memory.remove`.

Example: `mammoth agent memory remove sample 123`. Illustrative only: append `--yes` after observing an owned target.

Result: `AgentMemoryRemoveResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.message.set-request-kind`

Run: `mammoth agent message set-request-kind`. Exact input fields: `mammoth schema get agent.message.set-request-kind`.

Example: `mammoth agent message set-request-kind 'Summarize revenue by region' --input '{"request_kind": "sample"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentMessageSetRequestKindResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.plan.edit-proposal`

Run: `mammoth agent plan edit-proposal`. Exact input fields: `mammoth schema get agent.plan.edit-proposal`.

Example: `mammoth agent plan edit-proposal --input '{"plan_id": "resource-123", "action": "sample", "key": "Status"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentPlanEditProposalResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.projects.clear`

Run: `mammoth agent projects clear`. Exact input fields: `mammoth schema get agent.projects.clear`.

Example: `mammoth agent projects clear sample`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentProjectsClearResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.projects.set`

Run: `mammoth agent projects set`. Exact input fields: `mammoth schema get agent.projects.set`.

Example: `mammoth agent projects set sample --input '{"project_ids": [12, 15]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentProjectsSetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.publish`

Run: `mammoth agent publish`. Exact input fields: `mammoth schema get agent.publish`.

Example: `mammoth agent publish sample`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentPublishResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.roles`

Run: `mammoth agent roles`. Exact input fields: `mammoth schema get agent.roles`.

Example: `mammoth agent roles`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentRolesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.run.extend`

Run: `mammoth agent run extend`. Exact input fields: `mammoth schema get agent.run.extend`.

Example: `mammoth agent run extend resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentRunExtendResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.run.instance.list`

Run: `mammoth agent run instance list`. Exact input fields: `mammoth schema get agent.run.instance.list`.

Example: `mammoth agent run instance list resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentRunInstanceListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.run.instance.messages`

Run: `mammoth agent run instance messages`. Exact input fields: `mammoth schema get agent.run.instance.messages`.

Example: `mammoth agent run instance messages resource-123 resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentRunInstanceMessagesResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.run.instance.transcript`

Run: `mammoth agent run instance transcript`. Exact input fields: `mammoth schema get agent.run.instance.transcript`.

Example: `mammoth agent run instance transcript resource-123 resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentRunInstanceTranscriptResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

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

### `agent.run.retry`

Run: `mammoth agent run retry`. Exact input fields: `mammoth schema get agent.run.retry`.

Example: `mammoth agent run retry resource-123`. Illustrative only: append `--yes` after observing an owned target.

Result: `AgentRunRetryResult`; mutation `benign_mutation`, confirmation `prompt_or_yes`, wait policy `not_async`.

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

### `agent.run.units.list`

Run: `mammoth agent run units list`. Exact input fields: `mammoth schema get agent.run.units.list`.

Example: `mammoth agent run units list resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentRunUnitsListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.run.units.set`

Run: `mammoth agent run units set`. Exact input fields: `mammoth schema get agent.run.units.set`.

Example: `mammoth agent run units set resource-123 --input '{"step": 1, "kind": "sample", "units": [{"sample_key": "Status"}]}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentRunUnitsSetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.scratch.clear`

Run: `mammoth agent scratch clear`. Exact input fields: `mammoth schema get agent.scratch.clear`.

Example: `mammoth agent scratch clear sample 'Revenue report'`. Illustrative only: append `--yes` after observing an owned target.

Result: `AgentScratchClearResult`; mutation `destructive`, confirmation `prompt_or_yes`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.scratch.get`

Run: `mammoth agent scratch get`. Exact input fields: `mammoth schema get agent.scratch.get`.

Example: `mammoth agent scratch get sample 'Revenue report'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentScratchGetResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.scratch.list`

Run: `mammoth agent scratch list`. Exact input fields: `mammoth schema get agent.scratch.list`.

Example: `mammoth agent scratch list sample`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentScratchListResult`; mutation `read`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.scratch.set`

Run: `mammoth agent scratch set`. Exact input fields: `mammoth schema get agent.scratch.set`.

Example: `mammoth agent scratch set sample 'Revenue report' --input '{"content": "sample"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentScratchSetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

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

### `agent.team.set`

Run: `mammoth agent team set`. Exact input fields: `mammoth schema get agent.team.set`.

Example: `mammoth agent team set sample --input '{"team": {"agents": ["margin-watch"], "max_rounds": 4}}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentTeamSetResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.turn.cancel`

Run: `mammoth agent turn cancel`. Exact input fields: `mammoth schema get agent.turn.cancel`.

Example: `mammoth agent turn cancel resource-123`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentTurnCancelResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.

### `agent.update`

Run: `mammoth agent update`. Exact input fields: `mammoth schema get agent.update`.

Example: `mammoth agent update sample --input '{"name": "Margin watch"}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `AgentUpdateResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: untried; no live run recorded.
