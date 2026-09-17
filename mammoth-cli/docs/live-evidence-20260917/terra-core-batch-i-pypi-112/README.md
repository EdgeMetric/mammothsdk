# Core typed-transform batch I — PyPI 1.1.12

This bounded disposable-fixture run used public PyPI `mammoth-cli` 1.1.12
(wheel SHA-256 `135b3384742d66ca4168b5afc2762a9c2502263228d6ee1a45f38560abf81a2e`)
with `mammoth-io` 0.7.1, profile `expanded-live`, workspace 4 / project 3.
No retained dataset or view—including dataset 29/view 46—was changed.

## Owned lifecycle and typed transformation

The schema-documented URL import created exactly one disposable dataset (36,
job 167) and its returned ready view (52). Its exact display schema supplied
the `store_id` display column used by the typed filter command. `view transform
filter 52` was submitted with exact parent 36, `store_id EQ ST001`, and
`filter_type=SHOW`; its successful response recorded future/job identifier 169
(raw envelope SHA-256 `f2a16004284af104c16534f107641f3dcdee7e86943faa33a2626488a7d045af`).

The post-transform task list and pipeline-items read each observed one task,
ID 11. Exact-parent task get returned the same task under view 52 with status
`executed`; its raw envelope hash is
`d303d56e759a19d93a96d48e6ef4f71826fa706e66651d7ddd227f1a24462d1a`.
A read-only `view preview` limited to five rows and two columns produced the
semantic oracle that every returned first-column value matched the filter
predicate. No raw preview rows are retained.

The generic `view.task.add` route is structurally mapped by the OpenAPI
manifest to `AddTask` / `POST .../pipeline/tasks`, but its schema requires a
strict opaque `task_spec` union. The typed filter command is separately mapped
to `FilterOpsMixin.filter_rows` with no OpenAPI operation ID. Therefore this
run **does not prove** that the typed filter invoked generic `AddTask`, and no
raw task specification was guessed or submitted. `view.task.preview` likewise
requires such a task specification and was not called. REL-460 and REL-461
remain Unassessed.

Cleanup used only returned dataset 36 (`dataset delete 36 --yes`, job 170;
raw envelope SHA-256
`3cb78a4f2ad33d127b2d9312f7423a4e458086aaef97dc247183e1a1a91ffb11`). A
successful scoped dataset list no longer included 36. The post-delete get
capture and retained dataset 29 postcheck are stored as sanitized structural
records. No outcome was unknown and no fixture was retried.

## Matrix proposals (not applied)

| Row | Proposal | Reason |
|---|---|---|
| REL-461 `view.task.add` | Unassessed | Typed filter persisted a task, but manifest/SDK evidence does not prove it traversed generic AddTask; opaque task_spec was not used. |
| REL-460 `view.task.preview` | Unassessed | It requires an opaque task_spec; no raw task specification was inferred or submitted. |

This README preserves only nonsecret IDs, sanitized command intent, timestamps
in the JSON records, hashes, and semantic summaries; it retains no source rows,
task payload, or credentials.
