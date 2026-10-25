# ADR 0001: mammoth-cli 2.3 architecture (ver3)

- Status: proposed
- Date: 2026-10-23
- Epic: #307 (issues #309–#315). The MCP items (#308, #316) are parked until the CLI side is done.

## Context

mammoth-cli has 845 commands generated from manifests. Every command runs through
`runtime/executor.run`. That one function does all of the following:

- validates the output mode;
- refuses removed, embedded-only and pending commands, and unsupported dry runs;
- opens the run log and the shared services;
- calls the handler;
- special-cases `doctor` and the streamed `run` output (through `meta` keys);
- emits the envelope;
- prints update hints and syncs skills;
- raises `typer.Exit`.

The other ways in reuse that function by capturing what it prints:

- `mammoth run` uses `linecapture` and `redirect_stdout`.
- `embed.invoke` adds stdout guards and a `stray_output` error.

ver3 adds three things:

- a task layer (#309);
- an invocation journal with resume and undo (#310, #311);
- output schemas (#315).

All three would add more cases to that function. ver3 must also stay a production CLI. Startup cost is
guarded (`test_startup_cost.py`). The envelope contract is public. `embed` runs many users
concurrently in one process. The backend has no idempotency keys (except `agents.py`
`request_key`), and draft mode is per view and covers pipeline steps only.

### What the research says, and what it does not

The research notes are in `.context/ver3/research.md`. Callability Is Not Operability (2608.23628)
lists seven Agent-First Tooling (AFT) mechanisms. Against those, mammoth-cli is:

- **Strong** on structured outputs and verification.
- **Partial** on discovery and resumable invocation.
- **Weak** on effect semantics: no idempotency keys, no declared compensation.
- **Weak** on recoverable state: the run log is local and can't be used to resume or undo.

MCP-GRANITE (2609.24161) found that grouping tools by task class beats both one tool per operation
and a single monolithic tool. Both are preprints with small or mock setups. They decide what to
check, not what to build. Every choice below is justified by a problem in this codebase.

## Decision

### Structure: hexagonal (ports and adapters)

```
            driving adapters                      driven ports → adapters
  typer terminal ─┐                         ┌─ MammothGateway → SdkMammothService (exists)
  mammoth run ────┤                         ├─ JournalStore   → local JSONL (runlog grows into it)
  embed.invoke ───┼─► dispatch(Request) ────┼─ Confirmer      → TTY prompt | --yes | refuse
  task runner ────┘     │ interceptors      ├─ OutputSink     → stdout | captured list | embed call
                        ▼                   ├─ Clock, IdGenerator
               domain: contracts, policies, └─ (trace → User-Agent, see Telemetry)
               plans, bindings (pure)
```

- **Domain (pure, no I/O):**
  - operation contracts: the manifests, `mutation_class` and input contracts;
  - policies: confirm, dry-run and the expected-task guard;
  - plans and bindings (`runtime/bindings.py`);
  - lifecycle normalization.
- **Application:** `dispatch(Request) -> Outcome` (the envelope's value before rendering). This is the only use-case entry point, and it
  returns a value. It never prints and never raises `typer.Exit`.
- **Driving adapters:**
  - The terminal adapter is the only place that renders and exits.
  - `run` and `embed` take the returned `Envelope` directly, so stdout capture goes away.
  - The task runner calls `dispatch` once per step.
- **Driven ports:** `typing.Protocol` interfaces. The SDK service already is the gateway. The 845
  `handler(invocation)` functions are wrapped by one generic Adapter (`LegacyHandler`), so none of
  them changes in this ADR.

### Patterns, each tied to the problem it fixes

| Pattern | Where | Problem it fixes |
|---|---|---|
| Facade | `dispatch()`; the task layer over commands | Three ways in each re-run the executor and capture its output |
| Adapter | `LegacyHandler`; one driving adapter per surface | 845 handlers keep working unchanged |
| Ports as `Protocol` | gateway, journal, confirmer, output, clock | Tests build fakes per port, not monkeypatched modules |
| Chain of Responsibility | interceptors in `dispatch` | Hardcoded steps and special cases in `executor.run` |
| Command | `Request` (command id, inputs, flags, invocation id) | A call can be journaled, replayed and planned |
| Result value | `Envelope` returned, rendered once at the edge | `typer.Exit` raised from deep inside; stdout capture |
| Functional core, imperative shell | domain modules have no I/O | Most of ver3 is testable without fakes |
| Anti-corruption layer | lifecycle translator | Finished jobs read `done`, `ready` or `settled` depending on the command |
| Specification | confirm and mutation policies | Policy `if` chains spread across `confirm.py` and handlers |
| Interpreter + plan/apply | task plans with `Unresolved` placeholders | Dry-run refusals scattered per command; tasks can't be previewed |
| Append-only journal (event-sourcing lite) | one write-ahead record per invocation | The run log can't be used for resume (#310) or undo (#311) |
| Saga with compensation | multi-step tasks | Undo for a task means reversing completed steps in reverse order |
| Transactional outbox | journal writes before effects | A crash between effect and record loses the record |
| Idempotency key | `inv` sent as `Idempotency-Key` | `automation create` fires twice on retry; needs backend support |
| Strategy | output renderers, confirmers | Behaviour depends on mode and TTY |
| Conditional request (validator cache) | `mammoth.etag.ETagCache` port; memory in the SDK, disk in the CLI | Agents re-read the same lists and views across commands; the server already tags them |
| Repository | `JournalStore` | Journal storage can change without touching callers |

**Interceptor order:**

1. trace
2. validate output
3. refuse (removed, embedded, pending)
4. dry-run gate
5. policy and confirm
6. journal begin
7. shared services
8. handler
9. verify and normalize lifecycle
10. journal end

Rendering, update hints and skill sync stay in the terminal adapter, because they belong to that
surface and not to the use case.

**Strangler fig** is how we migrate, not a structure. It is built from the Facade and Adapter rows:
put the facade in front with no behaviour change, then move steps behind it one at a time, then
delete the old path.

**Rejected, because they don't fit a CLI process that lives for one command:**

- Full CQRS: two models over one data source.
- Event bus or actor model: no long-lived process to host them.
- DI container framework: one composition-root function is enough.
- Microkernel/plugin system: the registry and manifests already do this.
- Circuit breaker: it only pays off in a long-running process; the SDK retries reads with backoff.

### Telemetry: reuse `measures.request_log`, build nothing new

The backend already logs every API v2 request in `measures.request_log`:

- path, method, status and latency;
- user and workspace;
- the raw `User-Agent` (a `Text` column, set in `requestlog/service_v2.py`).

The CLI now writes one comment into that header on every request (`runtime/trace.py`):

```
mammoth-cli/2.2.100 (cmd=project.list; inv=97b9ee41d15d; surface=run; agent=claude-code) mammoth-io/0.8.51
```

- `cmd` is the manifest command id.
- `inv` is one id per invocation. All of its requests share it, and it is the local run log's
  `run_id`, so a user's log and the server rows join on it.
- `surface` is `terminal`, `run` or `embed`.
- `agent` comes from `MAMMOTH_AGENT` or from the variable a coding agent sets. An embedded call
  never sets it, because the host's environment is shared by every user it serves.
- Only identifiers are sent. The header is retagged per call, because one service serves every line
  of a `mammoth run`. This was verified live on koyal on 2026-10-23: two run lines over one
  connection carried two `cmd`/`inv` pairs.

This needs no backend change, no new endpoint and no opt-out. Nothing new is collected; existing
traffic is labelled. Example query (aggregate only: the table also holds full request and response
bodies, which must never be read for this):

```sql
SELECT substring(user_agent FROM 'cmd=([^;)]+)')                   AS cmd,
       count(DISTINCT substring(user_agent FROM 'inv=([0-9a-f]+)')) AS invocations,
       count(*) FILTER (WHERE status_code ~ '^[45]')                AS failed_requests,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY response_time_in_ms) AS p95_ms
FROM measures.request_log
WHERE user_agent LIKE 'mammoth-cli/%' AND received_at > now() - interval '7 days'
GROUP BY 1 ORDER BY invocations DESC;
```

Not covered: failures that never reach the server (usage errors, local validation, crashes before
the first request). `user_events` (`/workspaces/{id}/mm-ue`) could carry them later. It is
left out for now: it forwards to June and fires milestone events, so it would need a backend opt-out
for CLI events.

### Conditional reads: use every ETag the API gives (done)

API v2 tags its reads of workspaces, users, projects, folders, browse, datasets, views
and project resources, and answers `If-None-Match` with 304. The SDK sends back any tag it
was given, so a route the API tags later is covered with no change here. The tag
changes on every change event, a pipeline's status and row count included. This was
checked live on koyal on 2026-10-23: during a write, every state change came back 200 and
every unchanged poll came back 304. Any write the client sends empties its kept bodies.
`ETagCache` is a port: the SDK keeps bodies in memory, and the CLI adapter keeps them on disk
per credential, so the cache also works across processes. For `embed`, the host's `EmbedRuntime` keeps one budgeted
memory cache with one scope per caller credential. The scope is needed for correctness: a listing's
tag names the resource, but its body is filtered per user. This was verified live: a second embedded call got 304.

### Code mode (#310): steps in `mammoth run`, no Python sandbox

An agent chains commands by reading one result and writing the next call. `mammoth run` lines
can now do that in one process: a line has a `name`, later lines read its result as
`{{steps.<name>.data...}}` in `args`, `input` or `flags`, `when` skips a line, and `for_each`
runs a line once per item (`runtime/bindings.py`). Under `--dry-run` a line that reads a value
the preview did not make is planned (`data.planned`, `waits_on`), not failed.

We do not run agent-written Python (a sandboxed `exec` step), because:

- **The guarantees stay per command.** Every line goes through the same validation, confirm,
  dry-run and verify path as a single command, and its manifest policy applies. Arbitrary code
  could call the SDK directly and skip all of them.
- **A sandbox is a security product.** CPython has no in-process sandbox; a safe one needs a
  separate process with seccomp/containers on every OS the CLI ships to (Linux, macOS, Windows)
  and inside `embed` hosts that serve many users. That is a large attack surface for a CLI.
- **Plans need data, not code.** Dry-run plans, undo (#311) and resume (#310) need to know
  what a step will do before it runs. JSON references can be planned and journaled; code
  cannot.
- **Agents already have a shell and Python.** An agent that needs a loop the expressions
  cannot express can write it in its own environment around `mammoth run` or `embed`.

The expressions are deliberately small: dotted paths, `$keys`, `$first`, `$without`,
`$default`, and the conditions `eq`, `in`, `not`, `all`, `any`, `present`.

## Migration plan (strangler fig)

Each step ships alone, keeps the envelope contract, and passes the full CLI suite.

0. **Trace** (done): `runtime/trace.py`; `executor.run` opens a trace; the run log takes its id.
   **Conditional reads** (done): `mammoth/etag.py`, `runtime/etag_store.py`.
1. **Facade** (done): `runtime/dispatch.py` adds `dispatch(Request) -> Outcome` with the
   interceptors for output, refusals, dry-run gate and shared services. `executor.run` is the
   terminal adapter: it calls `dispatch`, then renders, logs and exits. The `producer` built by
   `app._execute` is the legacy-handler adapter, so no handler changed. Behaviour is identical.
2. **Interceptors** (done): a generic command runs through `runtime/leaf.py`'s chain:
   output check, refusals, dry-run gate, shared services, `admit_input` (argument, positional id,
   `--confirm` and `--input` checks, before anything is journaled), the journal, and
   `normalize_result` (the `verify` and `state` read-backs, health notes, `meta.opens`, next
   commands, compaction, and the exit status of a write whose read-back failed). `verify`'s
   `settled`/`pending`/`failed` outcome is the lifecycle translator. A command's confirmation
   prompt stays in its handler, which is the one place that knows what the prompt names; the
   generic `--confirm` check is in `admit_input`.
3. **run and embed adapters** (done as far as it goes): both receive the envelope value through a
   context variable (`linecapture`, `embedded`) and never parse printed text. `mammoth run` keeps
   its stdout redirect because Click prints help, version and usage errors itself, and embed keeps
   its stray-output guard because a handler or library can still print.
4. **Journal** (#310, port done): `runtime/journal.py` adds the `JournalStore` port and its file
   adapter, written by the `journal_writes` interceptor: a `begin` record before the handler (the
   outbox: a crash leaves a `begin` with no `end`, shown as status `unknown`), an `end` record with
   the exit, `meta.opens` and the undo lines. Resume (done): `mammoth run` and `recipe run` add a
   `plan` record (lines, shared flags, recipe inputs) and a `step` record per line (exit, and a
   named result up to 256 KB). `history resume GROUP` restores the finished steps and runs the rest
   through `run_lines`. A write with a `begin` but no `end` stops it (`resume_outcome_unknown`)
   until the caller checks the write and names `from_line`, because resending a write whose
   outcome is unknown could repeat it. Checked live on a dev server. Not done: the run log as a
   projection of the journal. The two stay separate files with the same ids (`run_id` = `inv`),
   so nothing reads one to rebuild the other.
5. **Task layer** (#309, done): a recipe in `discovery/recipes.json` with `inputs` and `run` is
   executable, with no second file: its `run` lines are `mammoth run` lines that read
   `{{inputs.NAME}}` and `{{steps.NAME.data...}}`, and `mammoth recipe run ID` runs them through
   `run_lines` (the same path as `mammoth run`), with `--dry-run` as the plan and one prompt or
   `--yes` before a recipe that writes. A contract test keeps each run line on a command the
   recipe's prose steps name. `how` returns the recipe's `run_command`, and `schema find` lists
   matching recipes before single commands, and so do `schema list` (a `tasks` list ahead of the
   families) and `capability find` (a `tasks` list ahead of the matches); the long tail stays
   one `schema list FAMILY` or `schema find` page away. Every recipe is executable (32): the
   first four ran end to end on a dev server (append-rows, upload-dashboard, export-csv,
   share-dashboard); the rest are covered by contract tests and a `--dry-run` plan test with
   mocked services, not yet by a live run: refresh-daily, blend-by-key, stuck-upload (reads
   only), export-powerbi, clean-data, cleanup-mine, upload-clean, join-files, lookup-column,
   add-calculated-column, extract-date-part, split-column, find-replace,
   fill-blanks-with-value, rename-columns, remove-duplicates, pivot-summary, top-n,
   filter-export-csv, export-xlsx, export-to-s3, email-view, dashboard-from-view,
   summarize-by, compare-views, refresh-now, undo-last-change, revert-view-version. Tasks that
   would destroy a view's rows (pivot-summary, top-n, filter-export-csv) work on a
   `view create --input '{"clone_from": ...}'` copy. An input may be a string, integer, array,
   object or `any` (text or number). `scripts/eval_task_calls.py` counts the calls per task
   with a recipe against step by step (`docs/task-call-eval.md`: 60 against 110 for the 32
   tasks, previews included; it counts calls, not accuracy). A partial step (exit 3)
   doesn't stop a recipe, so its read-back still runs. The live run found that an append read its
   target before the rows landed; `file upload` now waits for the target to read `ready`.
6. **Undo** (#311, done): each journaled write records its compensation as `mammoth run` lines, so
   undo needs no second interpreter. A trash is undone by a restore; an object listed in
   `meta.opens` with `created: true` goes to the trash, newest first; a `reversible_pipeline` edit
   applies the newest pipeline version read before the edit (versions are made on every change;
   the read asks `(id:desc)` because the API lists oldest first), or, on a view with no version
   yet, deletes the steps the edit added. `history undo` runs the lines as a saga through the
   normal command path, newest first, stops at the first failure and reports `partial`.
   `destructive` and `external_effect` writes record why they cannot be undone. Each command
   declares this in its manifest as `undo` (`inverse` with a `command`, `pipeline_version`,
   `trash_created`, `manual` with a `command`, or `irreversible` with a `reason`). The build script
   derives the default from `mutation_class`, the verb and the readback (`scripts/_undo_rules.py`),
   `commands/<group>.yaml` overrides it, `journal.compensation` only reads it, and a contract test
   fails a write with none. An `inverse` runs with the write's own positionals, so the two commands
   must take the same ones; a `manual` inverse needs an id from the result, so the journal names it
   in the reason and does not run it. Checked live on a dev server: a pipeline edit, an upload and a trash, each undone, and the undo of an undo.
   `view version apply` now waits for its job: without that, an undo returned before the view
   showed the restored steps.
7. **Idempotency** (done in the CLI): writes send `Idempotency-Key: <inv>`, and a retry resends
   the same key only where the server honours it; elsewhere the CLI reconciles before it retries.
   The backend middleware is mvc-service PR #7156, checked on a dev server.
8. **Delete the old path** (done): the producer `app._execute` built is gone, and so are the
   `STREAMED_META` and `EXIT_STATUS_META` meta keys and `dispatch`'s special case for `doctor`.
   A handler that names its own exit status, or printed its own envelopes, returns an `Outcome`
   (`run`, `recipe run`, `history undo`/`resume`, `doctor`).
9. **Module size** (#312, done): no module is over 1,500 lines. `commands/view_ops`,
   `commands/schema` (`examples`, `find`), `commands/dataset` (`find`, `create`) and
   `commands/dashboard` (`generated`, `workbook`) are packages with their shared helpers in a
   `_common` module where they had them; `app` is a package (`help_text`, `usage`, `options`,
   `tree`); `services/positionals.py` keeps the derivation and moved its spec and its override
   table to `positional_spec.py` and `positional_overrides.py`; the `support template` commands
   moved to `commands/support_template.py`. The `schema find` purpose tables are in
   `discovery/purposes.py`, and `HandlerResult` is defined once, in `commands/registry.py`.
10. **Generated manifests** (#313, done): `scripts/build_manifests.py` writes a
    record for every operation-backed or SDK-catalog command to
    `spec/manifests/commands.generated.yaml`. `commands/<group>.yaml` keeps only the fields that
    differ (and `unset`), or the full record of a command the generator doesn't make (38 of
    851). The loader merges the two, so the compiled records are unchanged; the hand-written YAML
    went from 37,720 lines to 6,711. Thin handlers are not generated, by decision: a command with no logic of its own already runs through one manifest-driven handler (`generated_dashboard`, 119 commands), so a generated function per command would add code rather than remove it.

## Consequences

- One use-case path for every surface. New cross-cutting behaviour is one interceptor, not edits
  across executor, run and embed.
- Command handlers don't change until a command wants a typed contract.
- Startup cost: `dispatch` and the interceptors are imported lazily, like today's runtime modules.
  `test_startup_cost.py` keeps guarding it.
- Risk: step 1 touches the path every command takes. The guard is the full non-live suite plus the
  `-m subprocess` tests on both Python 3.12 and 3.14, and a live koyal run of the epic's recipes.

## Review follow-ups (journal, undo, resume)

An independent review of the journal, `history undo`/`resume` and `run` bindings found these
rules; each has a test.

- **Created means new.** `meta.opens` marks an object `created` only when the call does not name
  it: an id in the input (`append_to_ds_id`, `target_ds_id`, `source_view_id`) or an argument is
  an existing object, and a command that edits its target never makes the view or dashboard in
  its result. An append is therefore not `trash_created`; its undo says rows cannot be taken out.
- **Uncertain outcomes.** The `end` record carries `outcome_unknown` for an interrupt, a timeout
  or a lost connection after the write was sent (error code, or `details.operation_state` of
  `outcome_unknown`/`running`). Resume treats it like a missing `end`: it refuses
  (`resume_outcome_unknown`) until `from_line` names where to start, and that choice settles the
  earlier unknowns (an `ack` record). A resume is a `resume` record linking its group to the run
  it resumed, so repeated resumes, `history show` and `history undo` use one group. A line that
  exited partial in a run that goes past partial lines is finished.
- **Run records** (`plan`, `step`, `item`, `resume`, `ack`) live in `journal/runs/<group>.jsonl`,
  not in the rotating file, and are pruned after 60 days. Every append holds `journal.lock`
  (`flock`, `msvcrt` on Windows) and is one `write`. Secrets are replaced before writing, by the
  same key rules the output uses; a line that holds or reads one is refused on resume
  (`resume_secret_needed`) and must be run by hand. The run log redacts the whole `--input`; the
  journal keeps the rest of the input so a resume can work.
- **Pipeline undo is guarded.** A pipeline edit's `end` record stores a fingerprint of the view's
  tasks right after it (type and parameters, not ids). The undo refuses
  (`view_changed_since_edit`) when the view differs, because applying the earlier version also
  drops later edits; `--input '{"force": true}'` overrides. The check costs one read on each side
  and is skipped when the read fails. An undo records each line it finishes and holds a claim
  (`undo-<inv>.lock`) so two undos of one write cannot run together.
- **Declined prompts and usage errors** are journaled (the journal and, for a pipeline edit, the
  version read run before the handler's checks) and then marked `nothing_sent`, which
  `history` hides. The reads are the cost; they stay because the handler cannot be asked early.
- **Not changed:** the SDK keeps its ETag bodies per client, keyed by URL and, with a
  `token_provider`, by the token sent; the CLI's disk store is already per credential.
  `view data profile` workers already run in a copy of the caller's context.
