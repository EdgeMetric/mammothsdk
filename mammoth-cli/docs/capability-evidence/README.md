# Capability evidence

This directory is the neutral, compact evidence boundary for the release
capability matrix. It intentionally contains row-level summaries, command
versions, exit statuses, and SHA-256 receipts only. Credential-bearing headers,
request bodies, and oversized live stdout/stderr transcripts are not product
documentation and are not retained here.

## Historical evidence index

The release matrix's historical evidence links now resolve to
[historical-release-index.md](historical-release-index.md). The matrix remains
the row-level source of truth for operation IDs, status, scope, and proof
limitations. Retired dated receipt paths remain recoverable from repository
history, but are not live documentation paths.

## Current batch

The 2026-09-17 published CLI 2.0.1 batch is summarized in
[capability-batch-201.md](capability-batch-201.md). It did not promote any row
to Full.

## 2026-09-18 sweeps

Dated directories hold one `results.jsonl` (one line per command id, quoted
in the matrix rows by SHA-256) and a `SUMMARY.md`:

- `read-sweep-20260918` — read-only routes.
- `dashboard-sweep-20260918` and `dashboard-reverify-20260918` — dashboard
  family before and after the 2.0.14 fixes.
- `haiku-e2e-20260918` — one autonomous end-to-end run (brief and report).
- `write-sweep-20260918` — 79 mutating routes in disposable projects; the
  CLI defects it found are fixed in 2.0.15 and marked "CLI defect fixed in
  2.0.15" in the matrix until re-run.
- `reverify-215-20260918`, `admin-read-sweep-20260918`,
  `backend-repro-20260918` — runs on the published 2.0.15: the fixed routes
  re-run, the admin/billing GET routes, and the backend handover.
- `reverify-216-20260918` — the routes fixed in 2.0.16 re-run on the
  working tree (conditional-format delete-all verified; `set-values` and
  `add-sql` probes behind the 2.0.17 / SDK 0.7.9 fixes).
- `haiku-cold-20260918` — a cold-start Haiku agent installing 2.0.16 from
  PyPI and running an ETL brief from the bundled skill alone; its report and
  the triage that led to 2.0.17.
- `ergonomics-sweep-20260919` — 27 calls with session defaults only on the 2.0.21 tree (owned projects 44–47).
- `haiku-etl-20260919` — Haiku 4.5 cold start on published 2.0.23 with a complex-join / cross-project brief; blocked by the release upload worker after two uploads (brief + report).
