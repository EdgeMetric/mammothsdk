# Core read-only verification — 2026-09-17

Profile: `expanded-live` (credential presence only; no secrets recorded)
Workspace: `4`; project: `3`; CLI: `1.1.5`; SDK: `0.7.1`

All commands below were read-only and used the observed retained resource
`view=46`, parent dataset `29` where applicable.

## Positive evidence

- Inspectable receipt: [`rel-217-version-get.json`](rel-217-version-get.json).
  `mammoth view version get 46 3 29 --profile expanded-live --project 3 --output json --no-input`
  returned exit code 0 and version `id=3`, `dataview_id=46`, with a structured
  `change_summary`, `created_at`, `created_by`, `modification_type`, `name`, and
  `note` response. This supports bounded Partial status for REL-217. Version
  receipts: [`version-cli.json`](version-cli.json) and
  [`version-sdk.json`](version-sdk.json).

## Explicit negative/ambiguity cases

- [`checkpoint-list-empty.json`](checkpoint-list-empty.json):
  `mammoth view checkpoint list 46 29 ...` returned exit code 0 with
  `checkpoints: []`; no checkpoint ID was available for a `checkpoint get`
  verification. REL-208 remains Unassessed.
- [`data-check-list-empty.json`](data-check-list-empty.json):
  `mammoth view data-check list 46 29 ...` returned exit code 0 with
  `data_checks: []`; no data-check ID was available for a `data-check get`
  verification. REL-210 remains Unassessed.
- [`ai-generation-info-403.json`](ai-generation-info-403.json):
  `mammoth view ai generation-info 46 ...` reached the retained view but the
  release endpoint returned HTTP 403 (`authorization_required`). This is not
  positive support evidence; REL-202 remains Unassessed.

No Full status is claimed for the pipeline-version or negative cases below.

## Full candidate qualification

The approved plan requires meaningful options, result/state, and applicable
lifecycle/error behavior. The inspectable folder evidence for REL-224 is in
[`folder-rel224-full.json`](folder-rel224-full.json): `fields=__full` returned
the ready folder state; wrong-project and missing-ID reads returned structured
authorization errors; the disposable folder was created, read, deleted with
`remove_contents=false`, and its name-filtered post-delete list was empty.
Only REL-224 is promoted to Full. This is a row-level claim; the folder family
is not Full because its other child rows remain Partial/Unassessed.
