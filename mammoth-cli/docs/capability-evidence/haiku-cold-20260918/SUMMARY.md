# Haiku cold-start end-to-end run (2026-09-18)

A Claude Haiku agent with no prior Mammoth knowledge installed `mammoth-cli`
2.0.16 from PyPI into a fresh virtualenv, learned the CLI from the bundled
skill only, and ran the brief in `BRIEF.md` (upload three messy CSVs, clean,
join, summarise, export, one dashboard, cleanup) against the release
workspace in a project it created (28) and deleted. Its own report is
`REPORT.md`; a first attempt earlier the same day aborted on a release
outage (every request 502/timeout) and is not counted.

Outcome: install, skill discovery, need-action resolution, 13 pipeline
tasks, two joins, CSV export, dashboard create/page/canvas save and full
cleanup all completed through the CLI. The delivered numbers were wrong, and
the agent did not notice.

## Triage

| Finding | Class | Resolution |
|---|---|---|
| `set-values` with a `condition` overwrote every row (all amounts 0, all regions "Unknown"); the agent then read the join as "146 orders had no matching customer" | **SDK bug** (`build_set_params` emitted the condition at task level, which the backend's VERSION 2 VALUES form ignores) | Fixed in SDK 0.7.9: the condition is folded into each value item. Verified live on probe project 29 (`reverify-216-20260918`). |
| `add-sql` rejected the summary query ("only select queries allowed") | **docs gap** (example used `FROM data`; SDK docstring used `__TABLE__`; the route wants the quoted table `"view:ID"` or the quoted display name) | Example, SDK docstring, SDK skill and the transforms recipe corrected; aggregation section added. |
| `view get` returned `"<unserializable View>"` after transforms | **CLI gap** (already tracked: the rich View object is not serialised by the generic path) | Unchanged in 2.0.17; `view preview` / `view data get` are the inspection routes. |
| `file upload` reported `status: "ready"` for a `need_action` dataset (observed by the operator, not the agent) | **CLI bug** | Fixed in 2.0.17: per-dataset status read back, with the file-settings route when action is needed. |
| First attempt: `project create --name` refused with only a schema pointer | **docs gap / CLI hint** | 2.0.17 names the positional or `--input` field; SKILL.md states the input model. |
| Dashboard PDF export needs a browser-hydrated payload | known limit | As documented. |
| Cleanup left nothing behind; `project list` back to baseline | ok | — |

The agent's friction log classified the `set-values` outcome as a data
fact rather than a defect. The transforms recipe now says to read the data
back after every value-changing step and that an unmatched join shows
nulls, not a filled default.
