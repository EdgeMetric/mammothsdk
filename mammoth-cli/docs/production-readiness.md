# mammoth-cli production readiness

Last updated 2026-09-19 for **mammoth-cli 2.0.27 / mammoth-io 0.7.12**. This is
the one page an agent or engineer reads to know what the CLI is, what is
proven, what is not, and where every claim's evidence lives. Update it with
every release; `docs/release-status.md` holds the per-release detail and the
PyPI hashes.

## Verdict

**Production-ready for the core ETL loop through an agent or a shell, against
the `app` endpoint, with the caveats in "Not ready / not proven" below.**

Proven end to end, live, from a cold start by a small model (Haiku 4.5) with
no notes other than the bundled skill: install → doctor → `project ensure` →
upload four CSVs → clean (discard duplicates, set-values, convert-type,
filters, text case/trim) → joins on mismatched and composite keys → math →
export CSV → deliver into a second project → pivot as the last step → read
back → delete only what it created and prove it is gone. Report:
`docs/capability-evidence/haiku-etl-20260919/REPORT-2.md`.

## What "ready" is backed by

| Claim | Evidence |
|---|---|
| Every command validates locally, returns one JSON envelope (compact when piped), maps SDK/HTTP failures to stable codes with a hint and recovery commands | `docs/reference/output-and-errors.md`; contract suite `tests/contract` (1490 tests) |
| Credentials never touch argv, logs or chat; profiles live in the OS keyring / `profiles.toml`; agents are told to have the operator run `auth login` | `docs/safety.md`, `docs/agent-prompt.md`, `tests/unit` (`test_auth*`, run-log redaction) |
| Destructive commands require `--yes --confirm ID`; high-impact ones confirm the target; discovery is refused for mutations without an exact parent | `docs/safety.md`, `references/safety.md`, `tests/contract/test_recovery_commands_agent_safe.py` |
| A transform that the backend cannot bind (missing column, wrong type) fails with `pipeline_reference_error` and the exact repair command, instead of exit 0 with a dead view | 2.0.25/2.0.26 entries in `docs/release-status.md`; live repro in `haiku-etl-20260919/REPORT-2.md` triage |
| Long operations wait up to 300 s (`--job-timeout`), timeouts hand back a `job get` recovery command, `outcome_unknown` is never retried blindly | `references/jobs-drafts.md`, `references/recovery.md` |
| Newer releases are announced in every envelope (`meta.update_available`), `mammoth upgrade --yes` upgrades the *running* install, `MAMMOTH_AUTO_UPGRADE=1` does it unattended | `docs/upgrade.md`; 2.0.26 entry (verified on a 2.0.24 venv) |
| Every published artifact is deterministic, scanned for local paths and secrets, and its PyPI digest is recorded | `docs/release-status.md` (one block per version) |
| Each release runs the unit + contract + realcode suites once (3212 passed at 2.0.27), ruff, mypy strict, and three `--check`-clean generators | commit messages; `docs/release-status.md` |

Evidence directory index: `docs/capability-evidence/README.md`. Row-level
status of all 528 API operations: `docs/release-capability-matrix.md`
(counts at 2.0.27: Full 1, Partial 260, Not supported 2, Unassessed 265 —
"Partial" means exercised live at least once in an owned project; it is a
bounded proof, not a qualification of every input shape).

## How an agent starts (the whole contract in four lines)

```bash
mammoth doctor                 # must pass; production is the app endpoint
mammoth skill show             # the guide; --input '{"file": "references/..."}' prints one reference
mammoth project ensure 'NAME'  # becomes the active project
mammoth schema get COMMAND_ID  # before any command not run before
```

`mammoth skill agents-md install` writes this into a repository's `AGENTS.md`
so later sessions start the same way. The full paste-ready prompt is in
`README.md` and `docs/agent-prompt.md`.

## Not ready / not proven (read before promising a deliverable)

Backend, on the `release` environment (the CLI sends what the web app sends;
these are recorded with tracebacks in `docs/release-status.md`):

- `view data-check update` returns 500 after applying (post-commit
  validation); read the check back before retrying.
- `browse` routes 500 on dashboards; `schedule` is `5GENR011 NOT_IMPLEMENTED`;
  `ai sql generate` needs an input table the route does not receive.
- `view export create` with a CSV/Postgres destination fails in the job with
  `'destination'` (REL-458); use `view export csv`.

CLI routes with **no live proof yet** that a real customer brief needs
(`docs/capability-evidence/ilg-feasibility-20260919.md`, section D):

1. **Cross-project delivery as a pipeline step.** `view export dataset` with a
   `target_ds_id` in another project has never been run live; both Haiku
   runs delivered by CSV + upload instead. Until proven, "add a parallel send
   from a production pipeline into a new project" is not a CLI promise.
2. **Add-only edits to a shared/production pipeline.** Typed transforms append
   at the end and never reorder, but there is no precondition (expected task
   count / version) that refuses when the pipeline changed since the read,
   and `view task add` takes an opaque `task_spec`.
3. **Dashboard measures beyond the typed surface.** KPI cards with
   `countDistinct` under a date filter, range filters and free-form widgets
   are reachable only through `dashboard canvas save` / the chat routes,
   neither proven for this; binding read-back (`dashboard canvas get`) is
   proven.
4. `view transform window`, month bucketing (`extract-date` component
   `month` / `add-sql DATE_TRUNC`) — commands exist, no live run recorded.

Operational (release host, not the CLI): the root volume of 10.1.100.131 was
100 % full on 2026-09-19, which raised the RabbitMQ disk alarm and left every
upload job in `processing`; 5.5 GB were reclaimed (82 % used). It needs a
bigger volume or `~/data/duckdb_efs` / `~/mmfiles/resources` moved.

## Next actions (ordered)

1. Prove item 1 above in two disposable projects and record it in the matrix
   (`view.export.dataset`, then `view.export.create` with an internal-dataset
   handler). This unblocks the ILG-style "parallel send" brief.
2. Add `--dry-run` (validate and print the resolved SDK call without a network
   call) and an `expected_task_count` precondition on pipeline mutations —
   both taken from the peer review of the Loops and PostHog agent CLIs.
3. Probe `dashboard canvas save` with a `countDistinct` KPI widget on a
   disposable dashboard; read it back with `canvas get` and `dashboard query`.
4. Re-run the ILG handoff in its reduced form (`F - SchoolPnL` + Overview)
   only after 1 and 3 have positive evidence, one production pipeline at a
   time, per the brief's own stop conditions.

## Where things live

- Per-release notes and PyPI hashes: `docs/release-status.md`
- Evidence runs (briefs, reports, `results.jsonl`): `docs/capability-evidence/`
- Row-level API status: `docs/release-capability-matrix.md` / `.json`
- Agent guide as shipped: `mammoth skill show` (source
  `mammoth_cli/bundled_skill/mammoth-cli/`)
- Error codes and envelopes: `docs/reference/output-and-errors.md`
- Safety model: `docs/safety.md`
- Release recipe: the 2.0.2x entries in `docs/release-status.md` (build with
  `SOURCE_DATE_EPOCH=1700000000 poetry build`, `twine check`, scan the wheel
  for local paths and secrets, upload, verify PyPI digests, record them, tag
  `cli-vX.Y.Z` on the source commit, push main and the tag)
