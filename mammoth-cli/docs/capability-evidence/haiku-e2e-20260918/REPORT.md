# Haiku end-to-end CLI run — release, workspace 4 / project 3 (2026-09-18)

Agent: Claude Haiku 4.5, CLI-only, no source access, profile `release`
(credentials in keyring; the agent never handled them). CLI 2.0.13 with SDK
0.7.4 in the CLI venv. Brief: `BRIEF.md`. Verbatim agent report below; the
capability-matrix fold uses only claims the agent backed with command output.

## Created ids (all deleted by the agent)
Datasets 44 (stores.csv), 45 (sales_2025.csv), 46 (targets.csv), 47 (Regional
Summary, from `view export dataset`); views 64, 65, 66, 67; dashboard 55.
Final `dataset list`: 28, 29, 30, 31, 33 only. Final `dashboard list`: 48 only.

## Steps and outcome
1. `file upload FILE --project 3` x3 → datasets 44/45/46 ready. (First attempt
   used a non-existent `--source` option: docs gap, now in the resources recipe.)
2. `view transform filter 65 --input '{"condition":{"column":"units","operator":"GTE","value":0},"dataset_id":45}'`
   → future 265. `view transform fill-missing 65 --input '{"column":"revenue","direction":"FIRST_VALUE","dataset_id":45}'`
   → future 271. Fill-missing propagates neighbours; a literal 0 needs
   `set-values` with an `IS_EMPTY` condition (docs gap, now in transforms recipe).
3. `view transform join 65` with `foreign_view: 64`, `foreign_dataset_id: 44`, on
   `store_id`, select `region` → future 273; second join against view 66 /
   dataset 46 on `region`, select `annual_target` → future 275.
4. `view transform pivot 65` group_by region, annual_target; SUM revenue, SUM
   units → future 277. `view export dataset 65 --input '{"dataset_name":"Regional Summary","dataset_id":45}' --yes`
   → dataset 47. Data read of dataset 47 showed four region rows
   (East/South/West/North) with annual_target, total revenue and total units.
5. `dashboard create-blank --input '{"params":{"dataview_id":67}}' --yes` →
   dashboard 55. `dashboard pages add 55 --input '{"body":{"params":{"pages":[{}]}}}' --yes --confirm 55`
   → page p2 auto-populated. `dashboard canvas save 55` with `{"canvas": {}}` →
   HTTP 400 "Field required: dataset" (the agent skipped the documented
   canvas get → save round-trip). `dashboard pdf export 55` with `{"data": {}}`
   → HTTP 400 "params.data must carry the client-hydrated DashboardData map"
   (backend precondition; not producible from the CLI).
6. `dashboard trash 55`, `dashboard delete 55 --yes`; `dataset trash`/`dataset delete --yes`
   for 44, 45, 46, 47. Baseline verified intact.

## Friction log (agent's classification, then triage)
| # | Observation | Agent class | Triage |
|---|---|---|---|
| 1 | `file upload --source` → `unknown_option` | docs gap | docs: resources recipe now states the positional |
| 2 | Filter operator values not obvious; `GTE` guessed and worked | my mistake | none |
| 3 | `fill-missing` cannot write a literal 0 | docs gap | docs: transforms recipe now points to `set-values` + `IS_EMPTY` |
| 4 | `canvas save` with `{"canvas": {}}` → "Field required: dataset" | CLI bug | docs: dashboards recipe now mandates get → save round-trip; `style_tokens` redaction that broke the round-trip fixed in 2.0.14 |
| 5 | `pdf export` needs client-hydrated data | CLI bug | backend precondition; matrix row Not supported from the CLI; manifest `known_restrictions` records it |
| 6 | `view export dataset` needed `--yes` | my mistake | expected (mutation policy) |
| 7 | `pages add` needs `--yes` and `--confirm 55` | CLI bug | expected (`confirm_target` policy); error hint already names both flags |
| 8 | `dataset delete` is asynchronous | my mistake | docs: resources recipe now says to re-read `dataset list` |

## Not done
PDF export (backend requires a browser-rendered payload). Everything else in
the brief completed, including cleanup.
