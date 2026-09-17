# Matrix proposals (for integration owner)

| Row | Proposed status | Evidence | Rationale |
|---|---|---|---|
| REL-199 | Partial | `active-user-list.json` | Exact-parent PyPI 1.1.11 read succeeded; retained view returned an empty active-user list. |
| REL-200 | Partial | `conditional-format-list.json` | Exact-parent PyPI 1.1.11 read succeeded; retained view returned an empty list. |
| REL-203 | Partial | `derivative-list.json` | Exact-parent PyPI 1.1.11 read succeeded; retained view returned an empty derivatives list. |
| REL-204 | Partial | `exportable-config-get.json` | Exact-parent PyPI 1.1.11 read succeeded; structural config returned, including five task entries. |
| REL-205 | Partial | `parameter-context.json` | Exact-parent PyPI 1.1.11 read succeeded; retained view returned empty parameter/snippet bindings. |
| REL-207 | Partial | `checkpoint-list.json` | Exact-parent PyPI 1.1.11 read succeeded; retained view returned an empty checkpoints list. |
| REL-209 | Partial | `data-check-list.json` | Exact-parent PyPI 1.1.11 read succeeded; retained view returned an empty data-check list. |
| REL-216 | Partial | `version-list.json` | Exact-parent PyPI 1.1.11 read succeeded; 11 versions returned on the documented single-page boundary. |

All rows remain Partial: one retained view, empty variants for most list routes,
and no continuation or negative-parent breadth. No errors occurred in this
batch.
