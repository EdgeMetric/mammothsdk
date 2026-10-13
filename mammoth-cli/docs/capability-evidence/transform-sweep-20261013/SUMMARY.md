# Live sweep of every `view transform` command, 2026-10-13 (koyal)

CLI 2.2.77 (mammoth-cli from origin/main 20c5eb14f7), SDK from the same tree, installed into a throwaway venv.

34 commands (the 32 of 2026-09-25 plus `first-name` and `update-column`), each once on its own fresh view cloned from `transform-sweep-20260925/fixture.csv` (koyal project 25654; lookup and join use `evals/two-files-dashboard/data/t_a.csv` and `t_b.csv`), read back with `view data get` against the known answer. `results.jsonl` holds input, observed values and notes. Harness: `harness/transform_sweep.py`. Fixtures were deleted afterwards.

Result: 32 of 34 match the known answer, 2 do not.

| command | old (09-25) | new | note |
|---|---|---|---|
| `view transform convert-type` | ok | ok |  |
| `view transform add-column` | ok | ok |  |
| `view transform set-values` | ok | ok |  |
| `view transform math` | ok | ok |  |
| `view transform text` | ok | ok |  |
| `view transform replace` | ok | ok |  |
| `view transform bulk-replace` | ok | ok |  |
| `view transform combine-columns` | ok | ok |  |
| `view transform copy-columns` | ok | ok |  |
| `view transform substring` | ok | ok |  |
| `view transform split` | ok | ok |  |
| `view transform json-extract` | ok | ok |  |
| `view transform extract-date` | ok | ok |  |
| `view transform date-diff` | ok | ok |  |
| `view transform increment-date` | ok | ok |  |
| `view transform small-large` | ok | ok |  |
| `view transform window` | ok | ok |  |
| `view transform fill-missing` | ok | ok |  |
| `view transform delete-columns` | ok | ok | first call refused for a missing --yes (confirmation_required); re-run with --yes on the same view, `code` gone, 13 columns left |
| `view transform rename-columns` | ok | ok |  |
| `view transform sort` | ok | ok |  |
| `view transform discard-duplicates` | ok | ok |  |
| `view transform filter` | ok | ok |  |
| `view transform limit-rows` | ok | ok |  |
| `view transform pivot` | ok | ok |  |
| `view transform unnest` | ok | ok |  |
| `view transform first-name` | (new) | FAIL | row 1 (' alice smith ', leading and trailing space) gives an empty first name; rows without padding are correct |
| `view transform update-column` | (new) | ok |  |
| `view transform lookup` | ok | ok |  |
| `view transform join` | ok | ok |  |
| `view transform add-sql` | ok | ok |  |
| `view transform crosstab` | ok | ok |  |
| `view transform generate-sql` | ok | ok |  |
| `view transform ai` | ok | FAIL | CLI exit 0, but `view pipeline get` shows execution_state runtime_error and the new column is empty in all 7 rows (the 09-25 run filled 3).  |
