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
