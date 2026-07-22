---
name: mammoth-cli
description: Drive the Mammoth Analytics platform from the command line. Use for authenticating, browsing projects and datasets, running pipeline transformations and exports, and any automated or agent task that needs deterministic JSON output and safe, confirmable mutations.
---

# Mammoth CLI

The `mammoth` command controls the Mammoth Analytics platform through the public
`mammoth-io` SDK. It is built for autonomous agents: every command supports
deterministic machine output, promptless operation, and stable error envelopes.

## Golden rules for agents

1. Always pass `--output json` and `--no-input`. Never rely on a prompt.
2. Discover, do not guess. Use `mammoth capability list` and `mammoth schema get`
   to learn a command before you run it.
3. Read the exit code, not the text. `0` ok, `2` usage, `4` auth, `5` not found,
   `6` conflict, `7` retryable, `1` other API error, `130` interrupt.
4. Confirm mutations explicitly. Destructive commands need `--yes`; high-impact
   commands also need `--confirm TARGET`. There is no interactive fallback under
   `--no-input`.
5. Never put a secret on the command line. Pass credentials through
   `mammoth auth login` (prompt or environment) and structured secrets through
   `--input`.

## Authenticate

```bash
export MAMMOTH_API_KEY=... MAMMOTH_API_SECRET=... MAMMOTH_WORKSPACE_ID=4
mammoth doctor --output json --no-input        # verify credentials + endpoint
```

Credentials resolve in this order: explicit login, then environment, then the
saved profile. The endpoint defaults to the `app-eu` server prefix. See
[references/auth.md](references/auth.md).

## Select a project

Most dataset, folder, view, and pipeline commands run inside a project.

```bash
mammoth context project use 180 --output json --no-input   # save the active project
mammoth project list --output json --no-input              # or pass --project 180
```

## Machine output and structured input

Every command returns `{schema_version, data, meta}` on stdout and a stable
`{schema_version, error:{code, message, hint, ...}}` on stderr. Feed multi-field
requests through one document:

```bash
mammoth view transform math 1039 --project 180 --output json --no-input \
  --input '{"expression": "price * qty", "new_column": "total"}'
```

See [references/machine-output.md](references/machine-output.md) and
[references/input.md](references/input.md).

## Safe mutations

```bash
mammoth dataset delete 2340 --project 180 --output json --no-input --yes
mammoth workspace delete 9 --output json --no-input --yes --confirm 9
```

See [references/safety.md](references/safety.md).

## Jobs, drafts, and cleanup

Long operations return a job; wait on it, then inspect the result. Draft mode
batches pipeline edits before submitting. Always delete resources you created in
a shared project. See [references/jobs-drafts.md](references/jobs-drafts.md) and
[references/recovery.md](references/recovery.md).

## Discover everything

```bash
mammoth capability list --output json --no-input     # every operation
mammoth schema list --output json --no-input         # every command's schema
mammoth schema get view.transform.filter --output json --no-input
```
