---
name: mammoth-cli
description: Drive the Mammoth Analytics platform from the command line. Use for authenticating, browsing projects and datasets, running pipeline transformations and exports, and any automated or agent task that needs deterministic JSON output and safe, confirmable mutations.
---

# Mammoth CLI

The `mammoth` command controls the Mammoth Analytics platform through the public
`mammoth-io` SDK. It is built for autonomous agents: every command supports
deterministic machine output, promptless operation, and stable error envelopes.

Examples in this skill are nonexhaustive. Discover the installed command
contract and compose the operation sequence required by the task.

For a cold start outside a repository or prior chat, begin with the portable
[task-start playbook](references/task-start.md). It explains pinned
installation, skill discovery, protected configuration, capability discovery,
verification, recovery, and cleanup.

**Evaluated/isolated-agent warning:** when a controller provides an
authentication broker or sidecar, use that controller path. Do not mount or
read a saved profile in the evaluated shell. If the broker/sidecar is absent,
stop before authenticated actions. The saved-profile examples below remain
for ordinary operator use and do not establish evaluated credential isolation.

## Golden rules for agents

1. Always pass `--output json` and `--no-input`. Machine output is automatic
   when piped or redirected, and `--no-input` turns on automatically off a
   terminal, but keeping both flags explicit is fine. Never rely on a prompt.
2. Discover, do not guess. Use `mammoth capability list` and `mammoth schema get`
   to learn a command before you run it.
3. Read the exit code and envelope, not the text. `0` is a reported success;
   `2` usage, `4` auth/authorization, `5` not found, `6` conflict, `7` a
   retryable read or known-job timeout that still needs inspection, `1` other
   API/job/artifact error, and `130` interrupt. Also inspect
   `details.operation_state` (`not_started`, `running`, `succeeded`, `failed`,
   or `outcome_unknown`).
4. Confirm mutations explicitly. Destructive commands need `--yes`; high-impact
   commands also need `--confirm TARGET`. There is no interactive fallback under
   `--no-input`.
5. Never put a secret on the command line. Pass credentials through
   `mammoth auth login` (interactive) or `mammoth auth login --input creds.json`
   (non-interactive), and structured secrets through `--input`.

6. Operate in an explicit scope: profile, workspace, project, dataset, and
   view/parent IDs come from observed reads. A dataset does not imply a usable
   default view; list views and choose one explicitly. Column fields and
   expressions use display names from the exact view schema, never backend
   internal names.

7. Follow discover → schema/scope → compose → verify → recover/cleanup. A
   read-back result, schema, artifact, or terminal job state proves the task;
   process exit 0 alone does not.

## Authenticate

Login is the only way to authenticate. Interactive login prompts for the API
key, the API secret, and then the workspace id (there is no `-w` flag):

```bash
mammoth auth login                               # prompts: key, secret, workspace id
```

For agents, log in non-interactively from a `0600` JSON file:

```bash
cat > creds.json <<'JSON'
{"api_key": "...", "api_secret": "...", "workspace_id": 4, "server_prefix": "app"}
JSON
chmod 600 creds.json
mammoth auth login --input creds.json --output json --no-input
mammoth doctor --output json --no-input          # verify credentials + endpoint
```

`server_prefix` is optional (default `app`). You can also pipe the document with
`--input - --input-format json`. Credentials resolve in this order: explicit
login, then the saved profile. The endpoint defaults to the `app` server prefix.
See [references/auth.md](references/auth.md).

## Select a project

Most dataset, folder, view, and pipeline commands run inside a project.

```bash
mammoth context project use 180 --output json --no-input   # save the active project
mammoth project list --output json --no-input              # or pass --project 180
mammoth view list DATASET_ID --project 180 --output json --no-input  # choose explicitly
```

## Machine output and structured input

Every command returns `{schema_version, data, meta}` on stdout and a stable
`{schema_version, error:{code, message, hint, ...}}` on stderr. Feed multi-field
requests through one document:

```bash
mammoth view transform math VIEW_ID --project PROJECT_ID --output json --no-input \
  --input '{"expression": "Unit Price * Quantity", "new_column": "Revenue"}'
```

See [references/machine-output.md](references/machine-output.md) and
[references/input.md](references/input.md).

For typed transforms, pipeline/task operations, workflows, and exports, read
[references/operations.md](references/operations.md). It explains how to use
the live command/schema contract without loading an exhaustive command catalog.

A transform that takes a nested request is driven the same way. Bulk-replace
maps many search values to one replacement, across one or more columns:

```bash
mammoth view transform bulk-replace VIEW_ID \
  --project PROJECT_ID \
  --input '{
    "columns": ["Status"],
    "mapping": [
      {"search": ["In progress", "Pending"], "replace": "Open"}
    ],
    "match_case": false,
    "match_words": true
  }' \
  --output json --no-input
```

- `columns` and `mapping` are required; each mapping needs `search` (a list) and
  `replace`.
- `match_case` defaults to `true`; `match_words` defaults to `false`.
- `condition` is optional (restrict the rows the replacement touches).
- Run `mammoth schema get view.transform.bulk-replace --output json --no-input`
  for the full request shape.

## Safe mutations

```bash
mammoth dataset delete 2340 --project 180 --output json --no-input --yes
mammoth workspace delete --output json --no-input --yes --confirm 9
```

See [references/safety.md](references/safety.md).

## Jobs, drafts, and cleanup

Long operations return a job. A command's `wait_policy` (see `mammoth schema
get`) tells you what to expect: `always_wait` and `start_or_wait` commands
resolve the job for you and return the final result; only a `returns_job`
command normally needs you to wait on the job id explicitly. A timeout with a
known job handle means inspect/wait that job, not resubmit the mutation. A
mutation transport failure without a confirmed handle is `outcome_unknown`:
reconcile the exact target before replaying it. Exit 7 is not blanket retry
permission. Draft mode batches pipeline edits before submitting. Always delete
resources you created in a shared project. See
[references/jobs-drafts.md](references/jobs-drafts.md),
[references/recovery.md](references/recovery.md), and
[references/handoff.md](references/handoff.md).

## Discover everything

```bash
mammoth capability list --output json --no-input     # every operation
mammoth schema list --output json --no-input         # every command's schema
mammoth schema get view.transform.filter --output json --no-input
```

## Keep the CLI current

```bash
mammoth upgrade --check --output json --no-input      # read-only: installed vs latest on PyPI
mammoth upgrade --yes --output json --no-input         # upgrade in place (requires --yes when non-interactive)
```

`mammoth upgrade` detects how the CLI was installed (uv tool, pipx, or pip) and
upgrades it; `--check` changes nothing. Pin an exact release with
`--version X.Y.Z`.
