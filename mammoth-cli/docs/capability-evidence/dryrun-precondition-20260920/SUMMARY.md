# Dry run, task-count precondition, window and extract-date (2026-09-20)

Release ws 4, owned project 57 (the ILG simulation fixture), CLI 2.0.30
working tree. `run.jsonl` is the command log.

## `--dry-run`

Exercised on `view transform filter`, `project delete` (no `--yes`),
`dataset delete`, `view export dataset` with `target_project_id`, `view get`,
`project ensure` (composed command) and `view transform extract-date`. Each
returned exit 0 with `data.dry_run: true` and `data.would_call` naming the
SDK symbol, the resolved arguments (condition compiled, parent dataset 122
resolved from memory) and, for View calls, `view_id`/`dataset_id`. Row counts
and the project list were unchanged afterwards; a bad column under
`--dry-run` still fails with `unknown_column` before the gate.

## `expected_task_count`

On view 144 (0 tasks): `expected_task_count: 3` on a filter →
`pipeline_changed`, exit 2, `details {expected 3, actual 0, task_ids []}`,
recovery `mammoth view task list 144`; `expected_task_count: 0` with
`--dry-run` passed the precondition and reported the call. `view task add`
with a wrong count is refused the same way before any request. On view 136
(3 tasks) `extract-date` with 3 and then `window` with 4 went through.

## Transforms proven

| command | check |
|---|---|
| `view transform extract-date` | `Month` (DATE) → `Month Number`: 9 / 10 / 12 for Sep / Oct / Dec |
| `view transform window` | running SUM of Sales Actual per Location by Month: all 12 Head Office values equal the local cumulative sum |

## Skill hygiene

`tests/contract/test_skill_hygiene.py` now asserts, for every bundled skill
file: no zero-width/bidi/soft-hyphen characters, no prompt-injection
phrasing (unless the line is the rule stating not to), no `curl … | sh`,
links only to `*.mammoth.io` or documentation example domains. The sweep
that motivated it found only `£ Σ — → ≤` as non-ASCII and no findings.
