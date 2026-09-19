# Agent handover and operation

[Documentation index](llms.txt)

This is the operational entrypoint for a shell-capable agent. The installer
puts the CLI and its bundled skill on the host; the skill gives focused routing
to recipes and command families. This guide explains the short loop an agent
uses to start, hand over, and recover a real task.

## Give an agent Mammoth access

The short form is the [agent prompt](agent-prompt.md): a paste-ready block
that has the agent install, read the shipped skill, authenticate through the
operator, and do everything else via `mammoth ... --output json --no-input`
in bash. The rest of this page is the same loop in detail.

Install once on the host:

```bash
curl -fsSL https://raw.githubusercontent.com/EdgeMetric/mammothsdk/main/mammoth-cli/installers/mammoth-install.sh | bash
```

The installer installs the CLI and skill for Codex, Claude Code, and Cursor.
Confirm and read the installed guidance before assigning work:

```bash
mammoth --version
mammoth skill list --output json --no-input
mammoth skill path --output json --no-input
```

Read the `SKILL.md` at the installed path reported above. Its cold-start
instructions are part of the local command contract; do not substitute a
repository copy or start discovery first.

For an exact release in a controlled evaluation, append `--version X.Y.Z`;
ordinary host installation needs neither option. See [Installation](installation.md).

Give the agent a task, acceptance criteria, and an explicitly authorized
workspace/project scope. Provision credentials through the host’s protected
secret mechanism or an interactive login. Do not place secrets in the task,
argv, transcript, checkpoint, or a source file.

## The operating loop

1. **Diagnose the profile first.** Run `mammoth auth status --profile
   PROFILE --output json --no-input`. This is a local presence check, not
   proof that credentials work. If the profile or credentials are missing,
   stop and tell the operator to run `mammoth auth login` in their own
   terminal (add `--server-prefix release` only for release); it uses hidden
   prompts. Wait,
   then re-check status. Do not ask for the key or secret in chat, and do not
   look for them in environment variables: the CLI does not read them from
   there. Use `--input` only with a protected `0600` file the operator handed
   you; see [Authentication](authentication.md). Then run `mammoth doctor --profile
   PROFILE --output json --no-input` and stop on any failed check. Before
   doctor, compare the endpoint in `auth status` with the intended target:
   production uses `app`; `release` is allowed only when explicitly intended.
   If it does not match, stop and select or create a separate correctly
   configured profile; do not diagnose or operate through the mismatched one.
   Every `view` command that changes, exports, or deletes data requires the
   exact parent `DATASET_ID`; only reads may omit it. Read it with
   `mammoth view get VIEW_ID --project PROJECT_ID --output json --no-input`.
2. **Discover the local contract.** Only after doctor succeeds, use `mammoth schema find
   QUERY` to locate a command and `mammoth schema get COMMAND_ID` before
   composing a request. `mammoth schema list` is the full CLI inventory.
   `mammoth capability list` is instead an API-binding inventory and can omit
   typed or local CLI routes.
3. **Resolve scope from reads.** List/get the authorized project, dataset, view,
   folder, or dashboard. Pass the observed `--project` and parents to every
   operation. A dataset is not a default view: list its views and select one by
   returned identity.
4. **Operate with structured data.** Use `--output json --no-input` and one
   `--input` document for nested fields. Column inputs and expressions use the
   exact display names returned by the selected view—not backend aliases.
5. **Verify the stated result.** Read back the resource, job, pipeline task,
   dashboard, or exported artifact against the task’s acceptance criteria.
   Exit zero alone does not prove the business outcome.
6. **Checkpoint or recover.** Keep a nonsecret handoff record after each
   material verified action. Inspect known jobs and reconcile an
   `outcome_unknown` mutation before a replay, cleanup, or new mutation.

The bundled [skill](../mammoth_cli/bundled_skill/mammoth-cli/SKILL.md) routes a
specific task to auth/scope, data/transform, dashboard/export, safety, or
handoff guidance. It intentionally does not make an agent load every reference
for a simple read operation.

## Machine contract

Use explicit flags in automation:

```bash
mammoth schema get view.transform.math --output json --no-input
mammoth project list --profile production --output json --no-input
```

Success is a JSON envelope on stdout; errors are a JSON envelope on stderr.
Branch on the stable error code, `details.operation_state`, recovery metadata,
and exit code—not prose. Preserve only nonsecret resource IDs, parent scope,
job handles, request IDs, and bounded evidence hashes.

## Safe interruption and handover

A timeout with a known job is **not** permission to resubmit: inspect it with
`mammoth job get JOB_ID` or continue with `mammoth job wait JOB_ID` in the same
scope. A transport failure during a mutation without a confirmed job/result is
`outcome_unknown`; re-list or read the exact target before any retry. Exit 7
and exit 130 likewise do not prove a mutation was not applied.

When transferring work, write the portable [nonsecret checkpoint
format](agent-handoff.md). The receiving agent validates the profile and scope,
checks the recorded versions and hash, re-reads each resource, reconciles every
pending job or unknown outcome, and then chooses the next safe operation.
There is no implicit resume command and a checkpoint never transfers authority.

## Focused next references

| Need | Read |
|---|---|
| First terminal workflow | [Quick start](quickstart.md) |
| Login, profiles, and scope | [Authentication](authentication.md) |
| Mutations and confirmations | [Safe mutation](safety.md) |
| Envelopes, exit codes, recovery | [Output and errors](reference/output-and-errors.md) and [Troubleshooting](troubleshooting.md) |
| Data import, transforms, dashboards, exports | [Bundled recipes](../mammoth_cli/bundled_skill/mammoth-cli/references/recipes/index.md) |
| Every installed command | [Command reference](reference/commands.md) or `mammoth schema list` |
| Cross-agent continuation | [Portable handoff](agent-handoff.md) |
