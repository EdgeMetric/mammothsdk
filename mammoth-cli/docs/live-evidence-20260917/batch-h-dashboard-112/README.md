# Batch H: owned dashboard lifecycle (published CLI 1.1.12)

Date: 2026-09-17 UTC  
Scope: profile `expanded-live`, workspace 4, project 3  
Artifacts: PyPI `mammoth-cli==1.1.12` (wheel SHA-256 `135b3384742d66ca4168b5afc2762a9c2502263228d6ee1a45f38560abf81a2e`), SDK `0.7.1` (wheel SHA-256 `41e606f1ce4705917449f6f926936abfb1f6e776b9339a42848370456fa7bf6e`).

## Result

The baseline contained only retained dashboard 48, sourced from retained view 46. The source-list read reproduced the documented HTTP 500 boundary and was not retried. One typed blank dashboard was created using observed `dataview_id=46`, returning owned dashboard ID 49. It was read back with source 46 and the owned title.

Typed QA settings were safely toggled `allow_viewer_qa=true → false → true`, with readback after each change confirming restoration. Generic `dashboard.update` was not run because its schema returns an un-waitable job under B13; no title mutation was needed after the typed create/readback.

Dashboard 49 was deleted with `--yes --confirm 49`. Final `dashboard.list` contains only retained dashboard 48, and a final read of 48 matched its baseline identity/title/source. A post-delete `dashboard.get 49` returned a non-retryable permission-style API error (HTTP 400, `4PERM002`) rather than a not-found envelope; list absence is the scoped cleanup proof, and no retry was made.

## Bounded proposals (matrix intentionally not edited)

* `REL-335 dashboard.create-blank`: propose **Partial** — typed owned creation from observed view 46, readback/source verification, and cleanup; no broad dashboard coverage.
* `REL-517 dashboard.qa.settings.set`: propose **Partial** — typed reversible false/true setting with independent readbacks.
* `REL-010 dashboard.delete`: propose **Partial** — exact owned-ID deletion and scoped list absence; post-delete get has an API permission boundary.
* `REL-326 dashboard.create`: **Unassessed** — not exercised because it returns an un-waitable job under B13.
* `REL-271 dashboard.update`: **Unassessed** — typed patch schema exists, but it also returns an un-waitable job and was not safely necessary.

All sanitized argv, UTC timestamps, stream hashes, and structural summaries are in `RESULTS.json`. No raw dashboard content, credentials, or retained-resource mutation is included.
