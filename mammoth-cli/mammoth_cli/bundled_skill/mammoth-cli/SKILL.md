---
name: mammoth-cli
version: 2.0.22
description: "Use Mammoth Analytics from a terminal: install or authenticate the CLI, discover its live command contract, and safely manage projects, data, views, pipelines, dashboards, exports, and handoffs."
---

# Mammoth CLI

Use this skill for Mammoth shell work, not for Python SDK integration. The
CLI is the contract: it validates every request locally, returns one JSON
envelope, and never needs a flag to do so when its output is piped.

## Start

```bash
mammoth doctor                          # auth, endpoint, connectivity, version; must succeed
mammoth project ensure 'PROJECT NAME'   # get-or-create; becomes the active project
```

`doctor` failing is a precondition failure, not a reason to try the business
command anyway. Production is the `app` endpoint; use `release` only when the
task names it, and check `meta.profile`/`auth status` `endpoint` match the
intended environment before doing anything. If no profile has credentials,
tell the operator the exact `mammoth auth login --profile PROFILE` command to
run in their own terminal and wait; never ask for a key or secret in chat,
never read one from a file or environment variable, never run `auth login`
yourself. If any envelope carries `meta.update_available`, run its `command`
before the next step.

## Defaults you do not repeat

- Piped stdout is compact JSON and prompts are off. Only in a session that
  is not piped, `export MAMMOTH_OUTPUT=json MAMMOTH_NO_INPUT=1` once.
- `project ensure` saves the active project; `--project` only overrides it.
  `MAMMOTH_PROFILE` / `MAMMOTH_PROJECT` also work as session defaults.
- The CLI remembers which dataset owns each view from any read (`view list
  DATASET_ID`, `view get VIEW_ID`, an upload). After that, no `dataset_id`
  on transforms, exports or deletes. If a command asks for the parent
  `DATASET_ID`, read the view once and repeat it; an explicit value always
  wins.
- Commands that start platform work wait up to 300 s for the job; on
  `timeout` use the `job get` recovery command printed, do not resubmit.

## Calling a command

- Ids are positionals; request fields are one `--input '{...}'` document;
  there are no per-field flags (`project create NAME`, not `--name`).
- `COMMAND --help` lists the input fields with types; `mammoth schema get
  COMMAND_ID` is the full contract (add `--input '{"full": true}'` for the
  JSON Schema); `schema list` is the family index, `schema list view` one
  family, `schema find WORDS` a search.
- Uploads return a **dataset** id; transforms, joins, exports and previews
  take the **view** id from `view list DATASET_ID`.
- Column inputs and expressions use the exact **display names** the view
  returns, never backend aliases.
- Destructive commands need `--yes --confirm ID`. Preserve requested
  deliverables; cleanup is exact-ID authorized and
  never means delete-all-owned-resources: delete only ids this run created,
  one per call, and read back that they are gone.
- A command whose schema lists `secret_fields` takes `--input FILE` (mode
  0600); secrets never go in argv, notes, checkpoints or replies.

## Verify before you report

- A success envelope proves the call, not the outcome. After a row-scoped
  change (set-values, filter, replace, join, fill) run `view data get
  VIEW_ID` (50 rows by default, `limit` to change) and check rows the
  condition should have touched and rows it should not have. Sample the
  target column *before* the change so the after-read has a comparison.
- A uniform result (every amount 0, every region "Unknown", most join rows
  unmatched) means the previous step went wrong; stop and re-inspect it.
- A timeout, exit 7 or interruption does not prove failure; reconcile an
  `outcome_unknown` (`job get`, `view task list`) before replaying.
- Run the [report checklist](references/report-checklist.md) before stating
  a number or calling a step done. When files here disagree,
  [capabilities](references/capabilities.md) wins over a recipe, and a recipe
  over the generated command catalog.

## Route only what the task needs

- **Cold start, task plan, or unsupported route:** [task start](references/task-start.md)
- **Login, profiles, and authorized scope:** [auth](references/auth.md)
- **Nested input, output envelopes, confirmations, jobs, or recovery:**
  [input](references/input.md), [machine output](references/machine-output.md),
  [safety](references/safety.md), or [jobs and drafts](references/jobs-drafts.md)
- **Import, resources, transforms, pipelines, dashboards, exports, or cleanup:**
  [recipes](references/recipes/index.md) — the
  [worked example](references/recipes/end-to-end.md) is the whole flow
- **Which id is which, appending rows, response shapes, and other one-off
  rules:** [operations](references/operations.md)
- **Something failed or you are unsure whether to continue:**
  [recovery](references/recovery.md) — failure modes by message and the
  stop-condition list
- **A known command family or exact command:** [command catalog](references/command-index.md)
  — a lookup for the one command you need, not upfront reading; each entry
  carries its release status line, and a `not supported` or `observed
  blocker` entry names the route to use instead
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
