---
name: mammoth-cli
description: "Use Mammoth Analytics from a terminal: install or authenticate the CLI, discover its live command contract, and safely manage projects, data, views, pipelines, dashboards, exports, and handoffs."
---

# Mammoth CLI

Use this skill for Mammoth shell work, not for Python SDK integration. Start
with the installed command contract rather than guessed routes or payloads:

```bash
mammoth schema find "TASK OR RESOURCE" --output json --no-input
mammoth schema get COMMAND_ID --output json --no-input
```

`schema list` is the complete CLI inventory. `capability list` is an
API-binding inventory and can omit typed/local CLI routes. Use deterministic
JSON (`--output json --no-input`) whenever another program or agent consumes
the result.

## Working rules

- Resolve workspace/project/dataset/view parents from reads; pass observed IDs
  and `--project`. A dataset does not select a default view.
- Use exact view-schema **display names** in expressions and column inputs,
  never backend aliases.
- Inspect the result after a mutation. A timeout, exit 7, or interruption does
  not prove it failed. Reconcile an `outcome_unknown` before replaying it.
- Keep secrets out of argv, task notes, checkpoints, logs, and responses.
- Preserve requested deliverables. Cleanup is exact-ID authorized and never means delete-all-owned-resources.

## Route only what the task needs

- **Cold start, task plan, or unsupported route:** [task start](references/task-start.md)
- **Login, profiles, and authorized scope:** [auth](references/auth.md)
- **Nested input, output envelopes, confirmations, jobs, or recovery:**
  [input](references/input.md), [machine output](references/machine-output.md),
  [safety](references/safety.md), [jobs and drafts](references/jobs-drafts.md),
  or [recovery](references/recovery.md)
- **Import, resources, transforms, pipelines, dashboards, exports, or cleanup:**
  [recipes](references/recipes/index.md) and [operations](references/operations.md)
- **A known command family or exact command:** [command catalog](references/command-index.md)
- **Pause or transfer to another agent:** [handoff](references/handoff.md)

## Handoff checklist

Before yielding work, write a nonsecret checkpoint with the intent and
acceptance criteria; authorized profile/workspace/project; observed resource
parents; verified evidence hashes; known jobs and unknown outcomes; remaining
objectives; and exact cleanup ownership. The receiving agent validates that
record and re-reads remote state before deciding what to do next. The handoff
is not a resume command or a grant of authority.
