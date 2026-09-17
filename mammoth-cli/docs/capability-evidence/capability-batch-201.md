# Published CLI 2.0.1 capability batch

Scope: approved saved `expanded-live` profile, workspace 4, project 3. No
credentials, request headers, or oversized response bodies are retained.

CLI: public PyPI `mammoth-cli==2.0.1`; `mammoth --version` exit 0. Published
wheel SHA-256:
`001ed77409aa44f405f47694ba9af0ad66cfd69b937a4860c3855fa66abe966d`.

Observed read-only results:

## REL-174 / REL-223

- `project list`, `project get 3`, `dataset list`, `folder list`, `folder root`,
  project pending-changes, and project resource-status exited 0.
- `dataset get 29` and `dataset file-settings get 29` exited 0.
- `view list 29`, `view get 46 29`, and `view data get 46 29` exited 0.
- Protected `dataset get 120` returned structured authorization failure (HTTP
  403); the protected ID was not modified.
- Invalid `view list` without a dataset ID returned deterministic
  `missing_argument` without dispatch.

The project-list and folder-list results above are alternate published CLI
2.0.1 evidence for REL-174 and REL-223. They remain Partial: one scoped
project and one empty folder page do not prove pagination breadth or all error
variants.

## REL-471

The external Tier B workbook records a bounded file-upload lifecycle: upload
returned dataset 364 ready, view 283 was listed and previewed with the exact
six-row fixture, delete job 325 completed successfully, and the final
dataset-get returned structured HTTP 403. The final absence and dataset-120
post-cleanup preservation were therefore not observed. REL-471 remains Partial;
no Full promotion follows.

## Owned fixture lifecycle

Owned fixture lifecycle (returned ID only): dataset 37/job 182 was created
ready; dataset/view/settings reads succeeded; typed file-settings update and
readback succeeded; dataset 37 deletion returned job 188; final dataset list
contained only pre-existing IDs 28, 29, 30, 31, and 33. Post-delete reads
returned structured authorization failures. Existing IDs 28--33 and 120, and
the parallel ETL resources, were not touched.

Rows informed: REL-174, REL-191, REL-192, REL-198, REL-201, REL-219, REL-223,
REL-226, REL-228, REL-443, REL-467, and REL-449. No row was promoted to Full;
the evidence remains bounded Partial because it lacks broad variant,
wrong-project, pagination, and authorization-boundary coverage.
