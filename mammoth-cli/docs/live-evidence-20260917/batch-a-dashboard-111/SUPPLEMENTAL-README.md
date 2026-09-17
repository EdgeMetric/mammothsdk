# Batch A supplemental reads

Using published CLI 1.1.11 / SDK 0.7.1 and `expanded-live`, the read-only
preset list exposed observed IDs (`stone`, `deepwater`, `editorial`, `ink`).
`dashboard style token list stone` then succeeded, returning a redacted token
payload. This supports a bounded REL-094 Partial proposal only; it is one
preset and does not expose token semantics.

`dashboard suggestion list 46` used the retained dataview whose correct parent
is dataset29. It exited successfully but returned `suggestions=null` with
`job_id=158`; no semantic suggestion result was available, so REL-095 remains
Unassessed. No job polling or mutation was performed.
