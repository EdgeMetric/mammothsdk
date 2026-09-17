# Core read-like batch F — PyPI 1.1.11

Scope: retained view 46 under observed parent dataset 29, workspace 4 / project
3; read-only calls only. Execution used public PyPI `mammoth-cli` 1.1.11
(wheel SHA-256 `25a811dad8d843731d719f20948ffe7df85dfb16a89f4cea1d8999925b54c962`)
and `mammoth-io` 0.7.1.

Before execution, `schema get` classified both POST routes `view.data.get` and
`view.data.query` as `effects: read`. The query schema explicitly requires
one-indexed offset and blocks `--all`; its live invocation used exact parent
29 with `limit=1, offset=1`. No query condition, AI generation, job, or
mutation was submitted.

`view-data-get-46-parent-29.json` succeeded with a structural 400-row page;
`view-data-query-46-parent-29.json` succeeded with a structural one-row page.
Both retain only UTC timestamp, sanitized argv, exit code, response hashes, and
structural summaries—no source rows or raw payloads.

`view.ai.generation-info` was schema-classified read but returned structured
HTTP 400 / `api_error`, so REL-202 remains Unassessed. `project
publish-credentials` was schema-classified read and invoked through the same
no-raw-output capture with documented `odbc_type=postgres`; it also returned
structured HTTP 400 / `api_error`, so REL-189 remains Unassessed. No credential
value was printed or retained.

`project.resource-dependencies` needs a nonempty exact `resource_ids` list.
No safe qualifying resource ID was observed in this batch, so REL-227 was not
called rather than guessing an identifier.

## Matrix proposals (not applied)

| Row | Proposal | Rationale |
|---|---|---|
| REL-449 | Partial | Schema-classified read POST succeeded for exact retained view 46/dataset 29 and returned a structural bounded page. One scope; not Full. |
| REL-451 | Partial | Schema-classified read POST query succeeded for exact retained view 46/dataset 29 at the documented `limit=1, offset=1` boundary. One query shape and no continuation; not Full. |
| REL-202 | Unassessed | Structured 400 `api_error`; no support claim. |
| REL-189 | Unassessed | Structured 400 `api_error`; no credential retained. |
| REL-227 | Unassessed | Required nonempty exact resource-ID list was not safely observed. |

