# mammoth-cli production readiness

Last updated 2026-09-25 (mammoth-cli 2.0.44, mammoth-io 0.7.18).

Read this page to learn what the CLI is, what is proven, and what is not. It
also says where the evidence for each claim is. Update it with every release.
`docs/release-status.md` holds the per-release detail and the PyPI hashes.

## Verdict

**Production-ready for the core ETL loop through an agent or a shell, against
the `app` endpoint, with the caveats in "Not ready / not proven" below.**

A small model (Haiku 4.5) proved this path live, end to end, from a cold
start, with no notes other than the bundled skill:

1. Install, `doctor`, `project ensure`, upload four CSVs.
2. Clean: discard duplicates, set-values, convert-type, filters, text case/trim.
3. Join on mismatched and composite keys; math; export CSV.
4. Deliver into a second project; pivot as the last step; read back.
5. Delete only what it created, and prove it is gone.

Report: `docs/capability-evidence/haiku-etl-20260919/REPORT-2.md`.

The two-file dashboard eval (`evals/two-files-dashboard`, three cold Haiku
runs on 2.0.41) scored 9, 8 and 6 of 10. Every run joined on the key it
found in the data, reported the match rate, and added revenue before the
dashboard. The open gap is blanks: each run left one blank column
undecided. 2.0.43 adds `mammoth project check`, which lists every open
finding (blanks included) before the report; it has not been through the
eval yet. See `docs/release-status.md` (2.0.42, 2.0.43).

A second live run (2026-09-19, `docs/capability-evidence/ilg-sim-20260919/`)
replayed a real customer rebuild brief on synthetic data. It proved:

- Sends from two source projects into a target project, as pipeline steps
  that re-run on upstream change.
- SQL conform per fact (`add-sql`) and joins into a mixed-grain consolidated
  table.
- Authored dashboards whose `countDistinct` card reads the true distinct
  count under a Month range filter (111 / 64 / 110 against the fixture key).
  The run read the bindings back by descriptor id.

## Evidence for "ready"

| Claim | Evidence |
|---|---|
| Every command validates locally, returns one JSON envelope (compact when piped), maps SDK/HTTP failures to stable codes with a hint and recovery commands | `docs/reference/output-and-errors.md`; contract suite `tests/contract` (1490 tests) |
| Credentials never touch argv, logs or chat; profiles live in the OS keyring / `profiles.toml`; agents are told to have the operator run `auth login` | `docs/safety.md`, `docs/agent-prompt.md`, `tests/unit` (`test_auth*`, run-log redaction) |
| Destructive commands need `--yes`; high-impact ones (project delete, access changes) also need `--confirm ID`; the CLI refuses discovery for mutations without an exact parent | `docs/safety.md`, `references/safety.md`, `tests/contract/test_recovery_commands_agent_safe.py` |
| A transform that the backend cannot bind (missing column, wrong type) fails with `pipeline_reference_error` and the exact repair command, instead of exit 0 with a dead view | 2.0.25/2.0.26 entries in `docs/release-status.md`; live repro in `haiku-etl-20260919/REPORT-2.md` triage |
| Long operations wait up to 300 s (`--job-timeout`), timeouts hand back a `job get` recovery command, `outcome_unknown` is never retried blindly | `references/jobs-drafts.md`, `references/recovery.md` |
| Every envelope announces a newer release (`meta.update_available`), `mammoth upgrade --yes` upgrades the *running* install, `MAMMOTH_AUTO_UPGRADE=1` does it unattended | `docs/upgrade.md`; 2.0.26 entry (verified on a 2.0.24 venv) |
| `--dry-run` on every API-backed command resolves inputs, parents and columns, then reports the SDK call instead of making it; the same gate stops any undeclared write. `expected_task_count` on pipeline writes refuses with `pipeline_changed` when the pipeline moved since the last read | `docs/safety.md`; `docs/capability-evidence/dryrun-precondition-20260920/`; `tests/unit/commands/test_dryrun.py` |
| The bundled skill carries no hidden characters, injection phrasing or unknown links | `tests/contract/test_skill_hygiene.py` (runs on every file of the skill) |
| Every published artifact is deterministic and scanned for local paths and secrets; `release-status.md` records its PyPI digest | `docs/release-status.md` (one block per version) |
| Each release runs the unit + contract + realcode suites once (4411 passed at 2.0.35), ruff, mypy strict, and three `--check`-clean generators | commit messages; `docs/release-status.md` |
| The ILG shape rebuilt on a second environment (prague ws 4) with fresh mock data and the production procedure (`--dry-run` then `expected_task_count` on every write; a stale count refused): 126 CLI commands, 68/68 checks against a Python key, upstream change propagated to a countDistinct card | `docs/capability-evidence/ilg-prague-20260921/SUMMARY.md` |
| CLI start-up 2.44 s → 0.51 s (libyaml, cached parsed manifests, command groups built on demand); the remaining ~2 s per call is TLS setup plus 1–1.3 s server time per request, measured identically on release and prague | `docs/troubleshooting.md`, `tests/unit/test_startup_cost.py` |

Evidence directory index: `docs/capability-evidence/README.md`. Row-level
status of all 528 API operations: `docs/release-capability-matrix.md`.
Counts at 2.0.30: Full 1, Partial 261, Not supported 2, Unassessed 264.
"Partial" means a live run exercised the operation at least once in an owned
project. It is a bounded proof, not a proof of every input shape.

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

The four gaps the ILG feasibility review listed
(`docs/capability-evidence/ilg-feasibility-20260919.md`, section D) and where
they stand after the live simulation (`ilg-sim-20260919/SUMMARY.md`):

1. **Cross-project delivery as a pipeline step — proven.** `view export
   dataset VIEW --yes --input '{"dataset_name": ..., "target_project_id": N}'`
   (SDK 0.7.13 `to_dataset(target_project_id=...)`) appends an
   internal-dataset export that re-materialises the target on every run.
2. **Add-only edits next to an existing send — proven, and now checkable.**
   The pre-existing export's sequence and execution times did not move, and
   every `view transform *` / `view task add` takes `expected_task_count`
   (refused with `pipeline_changed` when the live count differs) plus
   `--dry-run` to see the resolved call first. `view task add` still takes
   an opaque `task_spec`; prefer the typed transforms.
3. **Dashboard measures beyond the typed surface — proven through `canvas
   save`.** `countDistinct` KPI cards, `measure2` bars, derived ratio lines,
   tables, range/multi filters persist and bake; `descriptor-data` evaluates
   them under a filter. `pages add` and the chat routes pass the LLM guard,
   which can drop a unit it cannot evidence.
4. `add-sql DATE_TRUNC` month bucketing, `extract-date` (month component)
   and `window` (partitioned running SUM) — all proven with read-back
   (`dryrun-precondition-20260920/`).

Remaining CLI limits a brief may hit: one dataview per dashboard; PDF/video
export needs the browser; `series` on a derived-measure line was ignored in
the simulation; row volumes proven are hundreds, not the customer's
thousands.

Operational (release host, not the CLI): the root volume of 10.1.100.131 was
100 % full on 2026-09-19, which raised the RabbitMQ disk alarm and left every
upload job in `processing`; 5.5 GB were reclaimed and an hourly guard
(`~/utils/disk-guard.sh`, cron `17 * * * *`, log `~/logs/disk-guard.log`)
now trims caches, journals and rotated logs above 80 %. It sits at 80 % with
~6 GB free; the guard cannot go lower without touching data. Candidates for a
human decision: `~/mmfiles/resources/.git/lfs/objects` (1.5 GB, duplicates
the checked-out LFS files), `~/data/duckdb_efs/17` (2 GB, workspace data),
or a bigger volume.

## Next actions (ordered)

1. Run the ILG brief for real in its reduced form (`F - SchoolPnL` +
   Overview), one production pipeline at a time, with `--dry-run` then
   `expected_task_count` on every write, per the brief's own stop
   conditions; the routes are proven, the data volumes and feeds are not.
2. Look at why `series` on a derived-measure line is ignored by the
   dashboard bake, and at the LLM unit guard on `pages add`.
3. Host storage decision (LFS object cache / `duckdb_efs/17` / bigger volume).

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
