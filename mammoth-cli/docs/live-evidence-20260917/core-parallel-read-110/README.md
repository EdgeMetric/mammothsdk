# Core parallel read evidence — 2026-09-17

This evidence bundle covers only the six requested core read/contract rows:
REL-094, REL-096, REL-134, REL-135, REL-137, and REL-247.

- CLI: published `mammoth-cli` 1.1.10 (fresh supported-Python install)
- Profile: `expanded-live`
- Workspace/project scope: workspace 4, project 3
- Run time: 2026-09-17T11:19:51Z (UTC)
- Safety: read-only commands only; no ETL dataset/view/job IDs were supplied or touched.
- Output handling: only structural counts, metadata, schemas, and sanitized errors are recorded; no credentials or profile contents.

The two safe no-ID reads completed successfully. The other four rows require an
explicitly identified resource ID by contract; no safe non-ETL ID was available,
so those commands were not invoked. No 403, 500, or timeout occurred in this
pass. “Blocked” below means blocked by the row’s required input, not an observed
service failure.
