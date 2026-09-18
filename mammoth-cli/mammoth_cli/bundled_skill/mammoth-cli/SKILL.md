---
name: mammoth-cli
description: "Use Mammoth Analytics from a terminal: install or authenticate the CLI, discover its live command contract, and safely manage projects, data, views, pipelines, dashboards, exports, and handoffs."
---

# Mammoth CLI

Use this skill for Mammoth shell work, not for Python SDK integration. Complete
the authentication preflight below before using the installed command contract;
never guess routes or payloads:

Before any remote read or write, establish authentication. For ordinary
operator runs, determine the intended environment from the task: production
defaults to the `app` endpoint; use `release` only when explicitly named.
Check the selected profile with `mammoth auth status --output json --no-input`
and compare its reported `endpoint` to that target before running doctor. If
the profile is missing, credentials are absent, or the endpoint does not match,
stop and follow [authentication](references/auth.md); never silently reuse or
rewrite a profile from another environment. Then run `mammoth doctor
--profile PROFILE --output json --no-input` and require success before
discovering resources or operating on them. A failed status, login, or doctor
check is a precondition failure—not a reason to try the business command
anyway. If no matching profile has credentials, the operator must run
`mammoth auth login` themselves in their own terminal: tell them the exact
command, wait, then re-check `auth status`. Never ask for the key or secret
in chat, never read them from environment variables or files you were not
given, and never run `auth login` on the operator's behalf.

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
  and `--project`. A dataset does not select a default view. Every `view`
  command that changes, exports, or deletes data requires the exact parent
  `DATASET_ID` (trailing positional or `dataset_id` input field); only reads
  may omit it and discover the parent. Get it from `mammoth view get VIEW_ID`.
- Uploads and dataset creation return a **dataset** id. Transforms, joins,
  exports, and previews need a **view** id: run `view list DATASET_ID
  --project PROJECT_ID` to get it. See
  [resources](references/recipes/resources.md).
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
- **Whether a route is proven, known-blocked, or untried on release:**
  [capabilities](references/capabilities.md) — read it before promising a
  deliverable or reporting a failure as a backend fault
- **Pause or transfer to another agent:** [handoff](references/handoff.md)

## Handoff checklist

Before yielding work, write a nonsecret checkpoint with the intent and
acceptance criteria; authorized profile/workspace/project; observed resource
parents; verified evidence hashes; known jobs and unknown outcomes; remaining
objectives; and exact cleanup ownership. The receiving agent validates that
record and re-reads remote state before deciding what to do next. The handoff
is not a resume command or a grant of authority.
