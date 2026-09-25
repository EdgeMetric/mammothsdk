# Report checklist

Run this before reporting a number, declaring a step done, or handing over.
Every "yes" must point at a command you ran in this task and its response.

| Check | Evidence that satisfies it |
|---|---|
| State rows in and rows out for every step that can change row count (filter, discard-duplicates, join, limit, unnest, pivot) | `view data get` or `view get` (`row_count`) before and after the step, or the `view data get` around a set-values |
| Read back every value-changing transform | `view data get VIEW_ID DATASET_ID` (full page; `view data query` with `limit`/`condition` for a slice) after the job reached `success`; the sample shows the intended change and nothing else changed |
| No measure column is all-zero, all-null, or all one value after a transform | inspect the readback sample; an all-`0` / all-`Unknown` column means the condition or column mapping was wrong, not that the data is like that |
| Decide on every blank the deliverable uses | one report line for each `blank_values` entry (`project check` lists them all: from every view and dashboard): the column, the count, and filled, filtered, or kept and why. Kept is a decision only when you write it down |
| A join states its match rate and explains unmatched rows | row count before/after, `IS_EMPTY` filter count on a right-side column, and the key columns named exactly as both view schemas show them |
| Group counts add up | Σ of per-group counts from a pivot/crosstab equals the source row count (or nulls in the group key explain the difference) |
| Every job you submitted reached a terminal state | `job get JOB_ID` shows `success`; report anything else as failed/unknown, not done |
| List deliverable ids by type | project, dataset, view, export/dashboard ids with the command that created each |
| List cleanup ids and read each one back | one id per destructive call, each followed by a `list`/`get` that no longer shows it; the final list of what remains |
| Nothing in the report is a secret or an unredacted body | no keys, tokens, `--input` documents for `secret_fields` commands, or raw error bodies |
| Name every unknown outcome | any exit 7 / `outcome_unknown` with the id or job it may have created |

If you cannot satisfy a row, say so in the report instead of omitting it.
