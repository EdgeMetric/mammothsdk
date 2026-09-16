# Agent and CI usage

[Documentation index](llms.txt)

This guide describes the general operating contract for an external agent. The
examples are nonexhaustive: discover the installed command surface and compose
the sequence that the task requires. The CLI does not prescribe a fixed recipe.

For a fresh shell-capable agent with no repository or prior chat context, use
the shipped [portable task-start playbook](../mammoth_cli/bundled_skill/mammoth-cli/references/task-start.md).
It covers exact-version installation when the CLI is absent, skill discovery,
protected configuration, capability discovery, verification, recovery, and
cleanup without secrets or workbook-specific knowledge.

## The unattended loop

An agent should keep a small, nonsecret task record and repeat this loop as
observations change:

1. **Discover.** Search the capability catalog, then inspect the complete
   contract and example for the selected operation.
2. **Resolve scope and schema.** Authenticate a named profile. Resolve the
   workspace, project, dataset, and view explicitly. `--project` is an
   operation-local scope; it is safer than relying on a process's active
   context. A dataset does not imply a usable default view: list its views and
   choose one by the returned identity.
3. **Compose.** Pass IDs and parent IDs returned by reads. Name input columns
   by their display names exactly as returned in metadata or preview output;
   internal backend column names are not agent inputs. Use one structured input
   document for nested requests.
4. **Verify.** Read the affected resource and compare its current state,
   schema, row/sample, job, export, or dashboard identity with the acceptance
   criteria. Process exit 0 alone is not proof of the requested outcome.
5. **Recover or clean up.** On an interruption, timeout, conflict, or uncertain
   write, inspect the observed job/resource in the same scope before changing
   anything. Delete only resources recorded as created by this task, respecting
   dependencies and confirmation policy.

The loop is dynamic. A verification result can require a different operation,
additional scope, or a safe stop. Do not keep replaying a recipe after the
remote state has changed.

## Machine behavior

Use explicit machine flags in automation:

```bash
mammoth capability list --output json --no-input
mammoth schema get view.transform.math --output json --no-input
mammoth project list --profile production --output json --no-input
```

Piping or redirecting output already selects machine behavior, and
`--no-input` is automatic off a terminal, but explicit flags make a handoff
unambiguous. Success is one JSON envelope on stdout; errors are one JSON
envelope on stderr. `ndjson` is available for commands that document streaming.

Success has this shape:

```json
{"schema_version": 1, "data": {"id": 123}, "meta": {"command": "view get", "profile": "production", "workspace_id": 4, "project_id": 180, "pagination": null}}
```

Errors have a stable code and safe recovery metadata:

```json
{"schema_version": 1, "error": {"code": "...", "message": "...", "hint": "...", "details": {}, "request_id": null, "retryable": false, "authorization_required": false, "recovery_commands": []}}
```

Branch on `error.code`, `details.operation_state`, and the process exit code;
never parse prose. Preserve resource IDs, parent scope, job handles, request IDs,
and evidence hashes in the handoff record.

## Authentication and explicit scope

Provision credentials once through a protected file or an interactive terminal;
never put a secret in argv, a prompt transcript, a checkpoint, or a log:

```bash
chmod 0600 creds.json
mammoth auth login --input creds.json --output json --no-input
mammoth doctor --profile production --output json --no-input
```

The input file is consumed by the login command and should be removed or
rotated according to the runner's secret policy. See [authentication](authentication.md).
For every data operation, record and pass the exact `--project` and relevant
dataset/view parent. An active project is convenience context, not evidence
that a similarly named resource is the intended target.

## Structured input and display names

Discover the request schema before constructing input. This is a runnable,
display-name-only example (the IDs are placeholders for IDs returned by reads):

```bash
mammoth view transform math VIEW_ID --project PROJECT_ID \
  --input '{"expression": "Unit Price * Quantity", "new_column": "Revenue"}' \
  --output json --no-input
```

Do not copy an `internal_name` from an SDK response into a normal CLI request.
For joins, lookups, conditions, and expressions, use the displayed names from
the exact local and foreign view schemas. If a name is missing or ambiguous,
stop before mutation, refresh the schema, and select from the available names.

## Confirmations and effects

Inspect `mammoth schema get COMMAND_ID` before a mutation. It describes effects,
preconditions, confirmation, result identity, wait behavior, verification, and
known limitations. Destructive commands need `--yes`; high-impact commands also
need the exact `--confirm TARGET`. Under `--no-input` a missing confirmation is a
structured failure, never a prompt.

## Jobs, writes, and retries

Commands that wait for a known job return or expose its job handle. A timeout
while polling a known job means **running/known job**: inspect it with
`mammoth job get JOB_ID` or continue with `mammoth job wait JOB_ID` in the same
scope. A transport failure during a mutation without a confirmed handle means
**outcome_unknown**: the server may have committed it. Re-list or read the
target and reconcile before any create/replay. A retryable read can be retried
after honoring `Retry-After`; exit 7 is not a blanket permission to retry a
mutation. A conflict, authorization failure, or job failure requires its
documented correction, not repeated attempts.

On SIGINT, preserve the last observed handle and checkpoint the interrupted
state. Exit 130 means no terminal result was observed; it does not mean that a
remote operation was cancelled.

## Portable handoff

Write an atomic, nonsecret checkpoint when pausing or transferring ownership.
The format and receiving-agent procedure are in [agent-handoff.md](agent-handoff.md).
The receiving agent validates CLI/SDK/contract compatibility, authorized scope,
checkpoint integrity, and current remote state before choosing its own next
operation. There is no implicit resume subcommand.

## Cleanup and known gaps

Keep a dependency-aware inventory of resources created by the task. Verify
deletion or cleanup completion with a read/job result; do not delete arbitrary
inventory differences. Feature families or backend routes marked unsupported
by `capability list`/`schema get` are real capability gaps. Report them as
unsupported or backend-blocked instead of substituting a local calculation or
claiming success.

See [safe mutation](safety.md), [output and errors](reference/output-and-errors.md),
[troubleshooting](troubleshooting.md), and [portable handoff](agent-handoff.md).
