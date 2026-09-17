# Full-support candidate checklist (CLI 1.1.10)

This is an execution checklist, not a support claim. Live fixture work is
paused while ETL R6 owns project 3 datasets 18–22.

## Project list (REL-174)

- Positive: default list returns project 3 with stable envelope.
- Option: structured `{"limit":1}` returns one project; `{"limit":0}` returns
  an empty page with the requested limit.
- Error/contract: option misuse (`--limit`) returns deterministic
  `unknown_option`.
- Remaining review: confirm whether this read-only route's option and error
  assertions satisfy the project's Full bar; no promotion made.
- Evidence: `project-read-110/`.

## Dataset create/rename/delete (REL-443 / REL-292 / REL-044)

- Create the documented `weburl` fixture only; record ready job and exact
  returned ID.
- Rename through typed `dataset rename`; read back exact name and assert an
  invalid-name/target error.
- Delete only the returned ID; reconcile job and verify final absence.
- Preserve protected dataset 120 and record the postcondition.
- Full remains blocked until all assertions and cleanup are retained.

## Folder create/get/delete

- Create an owned folder; list/get positive response and scoped lookup.
- Exercise a safe field/filter option and an invalid ID response.
- Delete only the returned folder ID and verify final absence.
- Retain returned-ID ownership and cleanup evidence before any promotion.

## Dataview data (REL-201)

- Positive non-empty data response with row/header counts.
- Exercise documented `sequence`/`timeout` options and capture a stable
  validation or backend error variant.
- Read back view metadata, delete the owned dataset, and verify post-cleanup
  absence/error behavior.
- Current evidence is Partial: option variants remain unexercised.
