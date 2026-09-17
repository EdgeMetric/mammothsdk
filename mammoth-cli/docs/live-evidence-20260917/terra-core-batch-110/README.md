# Retained Core read batch — 2026-09-17

Sanitized, read-only release evidence for workspace 4 / project 3. No resource
was created, changed, or deleted. Each JSON record contains the UTC capture
time, exact sanitized argv, CLI version, exit code, SHA-256 hashes of the
unretained structured stdout/stderr, and only a structural response summary.

The initially available local 1.1.10 installation and local `dist` artifacts
are retained as diagnostic-only records and are **not** published-artifact
evidence. Likewise, records suffixed `-111` without `pypi` were run from the
local `dist/mammoth_cli-1.1.11-py3-none-any.whl`, SHA-256
`376c3ebc01071ad6efe804a7fabbd209a1bdaec8f211653b35607cb0a2dd82d5`.
That file differs from the public PyPI wheel and must not be described as
published.

The authoritative release records are suffixed `-pypi-111`: they were freshly
run from the wheel downloaded from PyPI for `mammoth-cli` **1.1.11**, SHA-256
`25a811dad8d843731d719f20948ffe7df85dfb16a89f4cea1d8999925b54c962`.
The matching published-wheel correct-parent captures cover view get, data get,
pipeline get, exports list, pipeline items, task list, task get, and dashboard
get.

## Correct-parent results

View 46 was read only with its observed parent dataset 29. Successful PyPI
1.1.11
calls were exports list (zero exports), pipeline items (one returned item with
the requested limit), task list (five returned tasks on its documented
single-page boundary), and task get for task 3 returned by that list. The
dashboard 48 get also succeeded and structurally returned one source. Dataset
gets for retained datasets 28, 29, 30, 31, and 33 succeeded under 1.1.10.

`view-get-46-invalid-parent-28-pypi-111.json` is deliberately separate negative
evidence: it returned structured HTTP 403 / `authorization_required`. It is
not authorization evidence for correct parent dataset 29 and must not be used
to downgrade the successful positive cases.

The earlier local-wheel dashboard-source record reached its endpoint but
returned structured HTTP 500 / `api_error`; it is diagnostic-only pending a
published-wheel reproduction and is not capability support.

No row is proposed as Full: all positives are one retained resource scope and
the list routes retain their documented pagination/contract boundaries.
