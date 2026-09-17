# Core read-only verification — 2026-09-17

Profile: `expanded-live` (credential presence only; no secrets recorded)
Workspace: `4`; project: `3`; CLI: `1.1.5`

All commands below were read-only and used the observed retained resource
`view=46`, parent dataset `29` where applicable.

## Positive evidence

- `mammoth view version get 46 3 29 --profile expanded-live --project 3 --output json --no-input`
  returned exit code 0 and version `id=3`, `dataview_id=46`, with a structured
  `change_summary`, `created_at`, `created_by`, `modification_type`, `name`, and
  `note` response. This supports bounded Partial status for REL-217.

## Explicit negative/ambiguity cases

- `mammoth view checkpoint list 46 29 ...` returned exit code 0 with
  `checkpoints: []`; no checkpoint ID was available for a `checkpoint get`
  verification. REL-208 remains Unassessed.
- `mammoth view data-check list 46 29 ...` returned exit code 0 with
  `data_checks: []`; no data-check ID was available for a `data-check get`
  verification. REL-210 remains Unassessed.
- `mammoth view ai generation-info 46 ...` reached the retained view but the
  release endpoint returned HTTP 403 (`authorization_required`). This is not
  positive support evidence; REL-202 remains Unassessed.

No Full status is claimed from this bounded evidence.
