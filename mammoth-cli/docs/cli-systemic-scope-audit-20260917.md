# CLI systemic scope and ergonomics audit — 2026-09-17

## Scope and method

This is a read-only, static audit of the manifest-driven Mammoth CLI surface at
the current worktree revision. It covers all **547** command manifests across
42 top-level families, the shared registration/dispatch/input/positionals
paths, and every command whose declared positional contract makes a parent
dataset optional. It did not use credentials or make live requests, so a
runtime outcome is claimed only where a unit/contract test or source path
proves it.

The command tree is built from the manifests in
`mammoth_cli/app.py:782-875`; positionals are centrally derived/overridden in
`mammoth_cli/services/positionals.py:91-869`; all normal leaves pass through
`app._execute` (`app.py:724-756`) and `SdkMammothService` (`services/sdk_service.py:88-121`).
That grouping is more meaningful than sampling 547 handlers one by one.

Commands by largest affected families: `view` 116, `dashboard` 104,
`support` 45, `billing` 23, `connector` 22, and `workspace` 20. The registry
contains 536 normal handlers; the remaining 11 are deliberately bespoke local
auth/config/context/upgrade routes, registered separately by the app. This
audit found no second generic resource-parent resolver outside the dataview to
dataset seam below.

## Findings

### P0 — optional dataview parents fan out to a project-wide discovery probe

**Proven static blast radius: 56 commands, all under `view.*`.** Each declares
an optional `dataset_id` and, when it is omitted both positionally and from
`--input`, reaches `_resolve_dataset_id` in `commands/view.py:141-166`. That
calls `PipelineAPI.find_dataset_for_dataview`, whose no-parent path calls the
project browse-and-probe resolver in `mammoth/api/pipeline.py:99-205`.

The affected commands group as follows:

| Family | Commands |
| --- | ---: |
| `view.export.*` | 18 |
| `view.checkpoint.*` | 5 |
| `view.data-check.*` | 5 |
| `view.derivative.*` | 5 |
| `view.version.*` | 5 |
| `view.conditional-format.*` | 4 |
| `view.active-user.*` | 2 |
| `view.data.*` | 2 |
| `view.exportable-config.*` | 2 |
| single-route families (`delete`, `get`, `parameter-context`, `pipeline.items-all`, `preview`, `restore`, `trash`, `update`) | 8 |

Of the 56, 17 are reads, 16 are benign mutations, 16 are external effects, 6
are destructive, and 1 is a reversible pipeline mutation. Thus this is not
only a read-path inconvenience: an omitted parent can precede delete, trash,
checkpoint/data-check mutation, version mutation, or export actions.

The historical failure is proven by the existing release evidence: a wrong
parent probe returning 403 terminated resolution before a later matching
dataset could be checked. The remediation currently being worked elsewhere is
appropriately SDK-level: CLI handlers, `ViewsResource`, `ExportsAPI`, and rich
`View` operations all converge on the same public resolver (`mammoth/client.py:110-127`,
`181-212`; `mammoth/api/exports.py:51-57`). Fixing only a CLI handler would
leave other CLI routes and SDK consumers exposed.

**Required regression matrix before release:** a target view after a wrong
parent yielding 404; a target after a wrong parent yielding 403; actual 403 on
the correct parent; nested-folder discovery; explicit `dataset_id` proving no
browse/probe; and a cold process per command. Test both read and destructive
CLI routes through the public service seam, but do not live-mutate a shared
project.

### P1 — documented “optional” scope is operationally mandatory in almost every example

**Proven static documentation/ergonomics mismatch: 54 of the 56 commands
above include the optional dataset parent in their generated `agent_example`.**
Only `view.exportable-config.get` and `.apply` omit it. The commands advertise
view-first convenience, but the examples themselves avoid that convenience in
54 cases because omitting the parent invokes the expensive, failure-sensitive
lookup. This is strong evidence that `dataset_id` is actually part of the
resource identity in normal automation.

The behavior is encoded in `POSITIONAL_OVERRIDES` at
`services/positionals.py:142-243` and `434-765`; the examples are generated
into `spec/manifests/commands/view.yaml`. The input form is also dual-sourced,
which means agents must learn two ways to express the same parent without a
clear policy on when discovery is acceptable.

**Recommended design decision:** make exact `DATASET_ID` mandatory for
mutating/destructive/non-idempotent view commands; retain omission only for
explicitly marked discovery/read commands, with a `--discover-parent` opt-in
if backwards compatibility requires it. Until then, say prominently in help
and schema that supplying the parent is the reliable form and that omission
performs project-wide discovery.

### P1 — the export family exposes the same parent inconsistently

**Proven static mismatch: 7 generic `ExportsAPI` routes accept `dataset_id`
only through `--input`, while 18 sibling typed export routes expose it as an
optional trailing positional.** The seven are `view.export.create`, `csv`,
`delete`, `get`, `publish-db`, `publish-db-update`, and `update`.

`view.export.list` has an explicit optional trailing parent, but the other
seven rely on generic signature derivation and have no `dataset_id` positional
(`services/positionals.py:871-891`; `services/input_fields.py:130-148`). Their
SDK methods nevertheless auto-resolve when the input field is omitted
(`mammoth/api/exports.py:59-101`, `132-160`, and analogous methods below).
Five of these seven are external-effect operations, one is a benign mutation,
and one is a read.

Reproduction without credentials: compare `mammoth schema get view.export.list`
to `mammoth schema get view.export.get`; both can carry a dataset parent, but
only the former advertises it in the command argument list. This produces
misleading examples and makes copy/paste workflows inconsistent.

**Fix:** define one export parent policy in the positional catalog and apply it
to all 25 export routes, including generic API exports. Do not silently add a
fallback/retry; explicit parent forwarding must bypass discovery.

### P2 — cache language overpromises across CLI commands

The resolver cache is correctly keyed by `(workspace_id, project_id,
dataview_id)` in `mammoth/api/pipeline.py:64-75, 137-143`, but it lives on a
single `MammothClient`. `open_service` builds and closes a new service/client
for every CLI invocation (`runtime/session.py:35-63`). Therefore the cache
cannot make a sequence such as `view preview`, `view update`, then `view
export` cheap: every process begins cold. This is a proven lifecycle fact, not
a correctness defect. It becomes material because the CLI documentation
encourages a set of separate commands while treating parent discovery as a
convenience.

Do not add a cross-process cache without an explicit expiry, scope key,
invalidation rules for moves/deletes, and a way to bypass stale entries.
Instead prefer explicit parent propagation in scripts and recovery commands.

### P2 — page-boundary residual in 403 confirmation (hypothesis)

The proposed 403-safe resolver confirmation lists a candidate dataset with
`limit=1000` and treats a short page as evidence of non-membership
(`mammoth/api/pipeline.py:175-202`). This is intentionally conservative. If a
wrong candidate has 1,000 or more views, the first full page cannot prove
non-membership and a 403 propagates rather than scanning another candidate.
That is safer than suppressing a genuine authorization failure, but it can
still reject a valid target in a high-cardinality dataset. The exact backend
pagination behavior has not been live-qualified, so this is a hypothesis,
not a reported regression. Add a fixture for a full first page and define the
desired continuation policy before claiming complete coverage.

## Negative results and boundaries

* The only project/default-scope resolution shared by all normal commands is
  deterministic: `--project`, then selected-profile project, then an explicit
  `project_required` error (`context/resolver.py:153-169`,
  `runtime/session.py:66-94`). I found no hidden project-id guessing or
  cross-project fallback.
* The error mapper describes recovery but does not replay requests
  (`services/mapping.py:62-82`); no blanket retry path was found in CLI
  dispatch. This audit did not qualify server-side idempotency.
* Input admission is shared and strict before a service is opened
  (`app.py:724-745`, `runtime/invocation.py:117-177`). The export discrepancy
  above is an interface consistency problem, not evidence that arbitrary
  unknown fields are forwarded.
* No live API tests, credentials, mutations, or release publication were
  performed. Passing manifest/contract tests proves local consistency, not
  tenant-specific authorization behavior.

## Evidence run

```text
poetry run pytest -q tests/contract/test_parity_manifest.py tests/contract/test_command_contract_pilot.py
28 passed
```

The command-surface counts and example/positional comparisons in this report
were generated by importing the manifest loader and `resolve_positionals` in
the project Poetry environment; no profile or credential was loaded.
