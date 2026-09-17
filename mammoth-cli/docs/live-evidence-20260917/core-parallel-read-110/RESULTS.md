# Per-row proposals

Evidence was collected with the published 1.1.10 CLI using `--profile
expanded-live --project 3 --output json --no-input`.

## REL-094 — Full Style bundle by id

- Contract: `GET /dashboards/v3/styles/tokens`; canonical operation
  `dashboard.style.token.list`; positional `id` is required.
- Result: **blocked_no_safe_parent_id**. No command was run because supplying an
  ETL or guessed style ID would violate scope.
- Proposal: retain as contract-mapped but not live-verified; classify as input-
  blocked, not 403/500/timeout.

## REL-096 — Curated template catalog

- Contract: `GET /dashboards/v3/templates`; canonical operation
  `dashboard.template.list`; no positional input.
- Command: `mammoth dashboard template list ...`
- Result: **success**. JSON envelope had `schema_version: 1`, data keys
  `formats`, `functions`, `industries`, `templates`, and `use_cases` (5 top-level
  categories), with workspace 4 metadata. No 403/500/timeout.
- Proposal: independent live read evidence for the catalog operation.

## REL-134 — Track multiple job ids

- Contract: `GET /jobs`; canonical operation `job.get-many`; required field
  `job_ids` (`list[int] | str`).
- Result: **blocked_no_safe_job_id**. No command was run; no ETL or guessed job
  identifier was supplied.
- Proposal: retain as contract-mapped but not live-verified; classify as input-
  blocked, not 403/500/timeout.

## REL-135 — Get job by id

- Contract: `GET /jobs/{job_id}`; canonical operation `job.get`; required
  positional `job_id` (integer).
- Result: **blocked_no_safe_job_id**. No command was run; no ETL or guessed job
  identifier was supplied.
- Proposal: retain as contract-mapped but not live-verified; classify as input-
  blocked, not 403/500/timeout.

## REL-137 — Fetch user preferences

- Contract: `GET /preferences`; canonical operation `user.preference.get`; no
  positional input.
- Command: `mammoth user preference get ...`
- Result: **success**. JSON envelope returned `data: {GLOBAL: {},
  WORKSPACE_PREFERENCES: {}}`, `schema_version: 1`, command metadata for
  `user preference get`, workspace 4. No 403/500/timeout.
- Proposal: independent live read evidence for user preference retrieval.

## REL-247 — Get segments/features

- Contract: `GET /workspaces/{workspace_id}/split-segments`; canonical operation
  `workspace.segment.list`; no positional input.
- Command: `mammoth workspace segment list ...`
- Result: **success**. JSON envelope had `schema_version: 1`, data key
  `segments` (one top-level collection), and workspace 4 command metadata. No
  403/500/timeout.
- Proposal: independent live read evidence for workspace segment retrieval.
