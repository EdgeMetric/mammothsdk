# Deliverable retention and cleanup authorization

Classify every resource before creating or deleting it. Record only the
nonsecret ID, type, parent, dependency, and intended retention class.

| Role | Meaning | Default handling |
|---|---|---|
| **Temporary** | Scratch input or disposable probe created only to test a route. | Delete only after the readback/evidence is complete and cleanup is explicitly authorized. |
| **Intermediate** | A child view, batch, task, job, or staging resource needed to build or verify another result. | Keep until the dependent result is verified; delete children before parents, only within the authorized scope. |
| **Retained deliverable** | The dataset, view, dashboard, export file, or other artifact the user requested. | Preserve for handoff. Never remove it as incidental cleanup. |
| **Protected** | Pre-existing, shared, production, baseline, or otherwise not created by this task. | Do not delete or overwrite without explicit authorization naming the exact target. |

Cleanup authorization is specific, not implied by “clean up” or by an ID
appearing in a list. Before a destructive call, confirm the user authorized
the resource type, exact IDs, parent scope, and dependency order. If any of
those are missing, leave the resource in place and report the pending cleanup.
Never use a blanket “delete all owned resources” operation to tidy a task.

When a request asks to preserve a dataset, dashboard, view, or export, mark it
**retained deliverable** before creating intermediates and carry its ID/path
through the final readback. A successful create or export is not permission to
delete its source or result. Verify the deliverable and its artifact before
cleaning temporary/intermediate resources.

The handoff/checkpoint format can carry these nonsecret classifications and
cleanup ownership; it is not a durable cleanup journal and does not transfer
credentials or authority.
