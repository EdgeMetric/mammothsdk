# Report checklist

Run this before reporting a number, declaring a step done, or handing over.
Every "yes" must point at a command you ran in this task and its response.

| Check | Evidence that satisfies it |
|---|---|
| Rows in and rows out are stated for every step that can change row count (filter, discard-duplicates, join, limit, unnest, pivot) | `view data get` or `view get` (`row_count`) before and after the step, or the `view data get` around a set-values |
| Every value-changing transform was read back | `view data get VIEW_ID DATASET_ID` (full page; `view data query` with `limit`/`condition` for a slice) after the job reached `success`; the sample shows the intended change and nothing else changed |
| No measure column is all-zero, all-null, or all one value after a transform | inspect the readback sample; an all-`0` / all-`Unknown` column means the condition or column mapping was wrong, not that the data is like that |
| A join states its match rate and explains unmatched rows | row count before/after, `IS_EMPTY` filter count on a right-side column, and the key columns named exactly as both view schemas show them |
| Group counts add up | Σ of per-group counts from a pivot/crosstab equals the source row count (or the difference is explained by nulls in the group key) |
| Every job you submitted reached a terminal state | `job get JOB_ID` shows `success`; anything else is reported as failed/unknown, not done |
| Deliverable ids are listed by type | project, dataset, view, export/dashboard ids with the command that created each |
| Cleanup ids are listed and were read back | one id per destructive call, each followed by a `list`/`get` that no longer shows it; the final list of what remains |
| Nothing in the report is a secret or an unredacted body | no keys, tokens, `--input` documents for `secret_fields` commands, or raw error bodies |
| Unknown outcomes are named | any exit 7 / `outcome_unknown` with the id or job it may have created |

If any row cannot be satisfied, say so in the report instead of omitting it.
