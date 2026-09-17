# Batch G: folder lifecycle (published CLI 1.1.11)

Date: 2026-09-17 UTC  
Scope: profile `expanded-live`, workspace 4, project 3  
Artifact: PyPI `mammoth-cli==1.1.11`, wheel SHA-256 `25a811dad8d843731d719f20948ffe7df85dfb16a89f4cea1d8999925b54c962`; SDK `0.7.1`, wheel SHA-256 `41e606f1ce4705917449f6f926936abfb1f6e776b9339a42848370456fa7bf6e`.

## Result

Project 3 had no folders at baseline. One disposable folder was created (folder ID `2`, resource ID `123`), read back, renamed with the typed `folder.update` request, read back again, and deleted with `remove_contents=false`. The final folder list was empty, matching the baseline. A post-delete `folder.get 2` returned structured API error `INVALID_FOLDER_ID` (HTTP 400); the CLI returned exit code 0 for that response, which is recorded as an observed CLI/error-surface limitation.

The folder move was not executed. Its schema requires `resource_ids` and optionally a target folder resource ID, returns an un-waitable job, and the project had no observed non-root destination; the root response has `id=0` and `resource_id=null`. No target was guessed. Bulk delete was not executed: it is destructive and accepts a list, while the single-owned-folder delete path was sufficient and had explicit confirmation controls.

## Post-delete error reproduction

The original live capture redirected stdout only, so the terminal displayed the structured error while the recorded exit code was misleading. A separate read-only reproduction captured both streams: stdout was empty, the structured `INVALID_FOLDER_ID` HTTP 400 envelope was on stderr, and the shell exit code was `1`. See `POSTDELETE-GET-REPRO.json`; it supersedes the earlier single-stream note.

## Bounded proposals (matrix intentionally not edited)

* `REL-307 folder.update`: propose **Partial** — typed rename succeeded and exact owned ID readback confirmed the new name; no broader field coverage.
* `REL-306 folder.move`: **Unassessed** — safe target/job verification was unavailable; no mutation was attempted.
* `REL-059 folder.bulk-delete`: **Unassessed** — destructive list operation intentionally not exercised.
* Adjacent `folder.create`, `folder.get`, `folder.list`, and `folder.delete`: propose **Partial** for the bounded owned lifecycle only; this does not establish broad resource or pagination coverage.

All command records, sanitized argv, UTC timestamps, exit codes, output hashes, and structural summaries are in `RESULTS.json`. Schema snapshots were queried offline from the published CLI; no credentials or raw payloads are included.
