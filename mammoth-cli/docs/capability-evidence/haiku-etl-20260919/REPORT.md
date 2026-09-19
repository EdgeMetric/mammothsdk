# Haiku 4.5 cold start on published CLI 2.0.23 — complex ETL brief (2026-09-19)

Agent: Claude Haiku 4.5, bash only, no prior notes; brief in `BRIEF.md`
(type-mismatched join keys, duplicate right-side keys, composite fx join via a
derived month, `amount_usd` math, cross-project delivery, pivot last). Run
12:30–13:15Z against release (`MAMMOTH_PROFILE=release`), 40 tool calls, ~61k
agent tokens. The agent's own report is condensed below; the operator's
verification follows it.

## What the agent reported

- Install and learn: venv + `pip install mammoth-cli==2.0.23` (~3 min);
  `skill path` → `SKILL.md` → `recipes/end-to-end.md` (~7 min). "The skill's
  references directory provided clear navigation … required no guessing."
- Session defaults held: no repeated `--profile/--output/--no-input`; active
  project from `project ensure` worked as documented.
- `project ensure 'haiku-etl-2023-src'` → project 48. `customers.csv` →
  dataset 97 (42 rows, ready), `orders.csv` → dataset 98 (186 rows, ready).
- `fx.csv` and `targets.csv`: three upload attempts each ended in `timeout`
  after 300 s with the job (693, 694, 699) still `processing`
  (`validate_scan_and_upload_files`); `job wait` on them timed out too.
- `view data get 119 98 --input '{"limit": 10}'` timed out (job 697);
  `view transform discard-duplicates 119` → `retryable_error` (ReadTimeout),
  then on retry `api_error` 4DTVW019 "The response generated is invalid".
- Steps 2–9 not attempted; `project delete 48 --yes --confirm 48` → 202,
  project still listed at the end.
- Verbosity note: "`view get` and `view data get` return massive JSON
  envelopes with complete dependency trees and metadata structures".
- Verdict (agent): "The Mammoth CLI and its documentation are sound … the
  backend service was unavailable/degraded during this session."

## Operator verification (same day)

- Jobs 693/694/699 were still `processing` at 13:20Z, as was job 667 from
  08:24Z. A new upload (job 706, 12:56Z) completed in under 45 s while they
  were stuck; the next four uploads (708–712, 12:59–13:05Z, including a
  two-column six-row file) stuck again. The release upload worker flaps;
  nothing file-specific was found. Backend, not CLI.
- Project 48 was gone by 13:25Z (403 on its resources), so the 202 was an
  asynchronous delete queued behind the same worker; `project list` right
  after a delete can still show the project.
- The agent used `view data get 119 98` (dataset id positional) although the
  parent cache made it unnecessary — harmless, the exact parent wins.

## Folded into 2.0.24

- `view get` asks the server for the brief field set (id, ds_id, name,
  status, row_count, column_count, metadata, pipeline state): 7.5 KB → 1.5 KB
  on a three-column view; `fields` (`"__full"`, `"__standard"`, a list) for
  more. `view list` records trimmed the same way; `full: true` keeps them.
  `fields` was accepted by the handler but missing from the contract, so
  strict validation had rejected it.
- Prompt and upload recipe: the job budget is `--job-timeout` (300 s by
  default), not `--timeout`; a second upload of a stuck file queues a second
  job.

Not achieved: the tricky-join and cross-project steps themselves. Re-run the
brief when release's upload worker is stable.
