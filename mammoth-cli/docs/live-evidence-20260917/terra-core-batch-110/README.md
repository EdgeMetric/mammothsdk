# Retained Core read batch — 2026-09-17

Sanitized, read-only release evidence for workspace 4 / project 3. No resource
was created, changed, or deleted. Each JSON record contains the UTC capture
time, exact sanitized argv, CLI version, exit code, SHA-256 hashes of the
unretained structured stdout/stderr, and only a structural response summary.

The initially available published wheel was `mammoth-cli` **1.1.10**; its
successful correct-parent captures are `view-get-46-parent-29.json`,
`view-data-46-parent-29.json`, and `view-pipeline-get-46-parent-29.json`.
All files suffixed `-111` were freshly executed with published
`mammoth-cli` **1.1.11** (wheel SHA-256
`376c3ebc01071ad6efe804a7fabbd209a1bdaec8f211653b35607cb0a2dd82d5`).

## Correct-parent results

View 46 was read only with its observed parent dataset 29. Successful 1.1.11
calls were exports list (zero exports), pipeline items (one returned item with
the requested limit), task list (five returned tasks on its documented
single-page boundary), and task get for task 3 returned by that list. The
dashboard 48 get also succeeded and structurally returned one source. Dataset
gets for retained datasets 28, 29, 30, 31, and 33 succeeded under 1.1.10.

`view-get-46-invalid-parent-28-111.json` is deliberately separate negative
evidence: it returned structured HTTP 403 / `authorization_required`. It is
not authorization evidence for correct parent dataset 29 and must not be used
to downgrade the successful positive cases.

`dashboard-source-list-111.json` reached its endpoint but returned structured
HTTP 500 / `api_error`; it is recorded as a server result, not capability
support.

No row is proposed as Full: all positives are one retained resource scope and
the list routes retain their documented pagination/contract boundaries.

