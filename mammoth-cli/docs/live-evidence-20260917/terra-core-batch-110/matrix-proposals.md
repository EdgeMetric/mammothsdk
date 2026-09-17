# Matrix proposals (for integration owner)

| Row | Proposed status | Evidence | Rationale |
|---|---|---|---|
| REL-198 | Partial | `view-get-46-parent-29.json` | Correct-parent view 46 / dataset 29 read succeeded with CLI 1.1.10; separate wrong-parent 28 case is a 403 negative. Single retained scope only. |
| REL-201 | Partial | `view-data-46-parent-29.json` | Correct-parent data read succeeded with a structural 400-row page in CLI 1.1.10. No pagination breadth or independent oracle. |
| REL-206 | Partial | `view-pipeline-get-46-parent-29.json` | Correct-parent pipeline state read succeeded in CLI 1.1.10. Single retained scope. |
| REL-211 | Partial | `view-export-list-46-parent-29-111.json` | Correct-parent export-list request with input limit 1 succeeded in CLI 1.1.11 and returned an empty exports page. No non-empty export or continuation proof. |
| REL-213 | Partial | `view-pipeline-items-46-parent-29-111.json` | Correct-parent pipeline-items request with input dataset 29 and limit 1 succeeded in CLI 1.1.11. It returned one item; no continuation traversal. |
| REL-214 | Partial | `view-task-list-46-parent-29-111.json` | Correct-parent task list succeeded in CLI 1.1.11 and returned five tasks. Command contract remains single-page. |
| REL-215 | Partial | `view-task-get-46-task-3-parent-29-111.json` | Task 3 was first observed in the successful retained task list and task get then succeeded with exact parent dataset 29 in CLI 1.1.11. One task only. |
| REL-107 | Partial | `dashboard-get-48-111.json` | Retained dashboard 48 get succeeded in CLI 1.1.11 and structurally returned one source. One retained dashboard only. |
| REL-080 | Unassessed | `dashboard-source-list-111.json` | Endpoint returned structured HTTP 500 / `api_error`; do not treat as support. |

All positive rows remain Partial. The separate `view-get-46-invalid-parent-28-111.json` is an invalid-parent 403 control, not a promotion or authorization conclusion.
