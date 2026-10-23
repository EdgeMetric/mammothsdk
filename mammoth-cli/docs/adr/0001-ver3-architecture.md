# ADR 0001: mammoth-cli 3.0 architecture

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
- **Application:** `dispatch(Request) -> Envelope`. This is the only use-case entry point, and it
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

## Migration plan (strangler fig)

Each step ships alone, keeps the envelope contract, and passes the full CLI suite.

0. **Trace** (done): `runtime/trace.py`; `executor.run` opens a trace; the run log takes its id.
   **Conditional reads** (done): `mammoth/etag.py`, `runtime/etag_store.py`.
1. **Facade:** add `dispatch(Request) -> Envelope` and `LegacyHandler`. `executor.run` becomes the
   terminal adapter: it calls `dispatch`, then renders and exits. Behaviour is identical.
2. **Interceptors:** move the steps out of `executor.run` in the order above, one PR per group:
   refusals, dry run, policy, verify, lifecycle.
3. **run and embed adapters:** take the `Envelope` from `dispatch`. Delete `linecapture`'s stdout
   redirect and embed's stray-output guard where nothing still prints.
4. **Journal** (#310): add the `JournalStore` port. The run log becomes a projection of the
   journal. Add resume of a running invocation by `inv`.
5. **Task layer** (#309): recipes in `discovery/recipes.json` become executable plans, with one
   definition per recipe and no second file. Plans are interpreted over `dispatch`, using
   `runtime/bindings.py`, with plan/apply.
6. **Undo** (#311): add compensation per step, as a saga over the journal. It covers only what is
   reversible (`reversible_pipeline`, draft mode). `destructive` and `external_effect` steps are
   refused in an undoable task unless confirmed.
7. **Idempotency:** send `Idempotency-Key: <inv>` on writes once the backend honours it (backend
   issue to open).
8. **Delete the old path:** `executor.run`'s inline steps and the `STREAMED_META` and
   `EXIT_STATUS_META` meta keys.

## Consequences

- One use-case path for every surface. New cross-cutting behaviour is one interceptor, not edits
  across executor, run and embed.
- Command handlers don't change until a command wants a typed contract.
- Startup cost: `dispatch` and the interceptors are imported lazily, like today's runtime modules.
  `test_startup_cost.py` keeps guarding it.
- Risk: step 1 touches the path every command takes. The guard is the full non-live suite plus the
  `-m subprocess` tests on both Python 3.12 and 3.14, and a live koyal run of the epic's recipes.
