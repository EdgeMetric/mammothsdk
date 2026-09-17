# REL-461 typed-filter endpoint trace

This source trace connects the bounded live typed-filter result in Batch I to
the generic AddTask OpenAPI endpoint, without asserting that the opaque raw
`view task add` input contract is generally usable.

1. The CLI registry binds `view.transform.filter` to
   `view_transform_filter` in
   [`registry.py`](../../../mammoth_cli/commands/registry.py:629).
2. `view_transform_filter` dispatches method `filter_rows` in
   [`view_ops.py`](../../../mammoth_cli/commands/view_ops.py:508) and the
   dispatcher resolves the exact dataset parent before `service.call_view` in
   [`view_ops.py`](../../../mammoth_cli/commands/view_ops.py:191).
3. `FilterOpsMixin.filter_rows` builds the typed filter task and calls
   `self._add_task` in
   [`_filter_ops.py`](../../../../mammoth/_mixins/_filter_ops.py:20).
4. `View._add_task` calls `self._client.pipeline.add_task(self.id, task_spec,
   self.dataset_id)` in [`view.py`](../../../../mammoth/view.py:316).
5. `PipelineAPI.add_task` issues `POST {base}/tasks` in
   [`pipeline.py`](../../../../mammoth/api/pipeline.py:321), where its base
   resolves to the dataset/dataview pipeline route. The OpenAPI manifest maps
   that `POST .../pipeline/tasks` identity to operation `AddTask` / REL-461
   and canonical command `view.task.add`.

Batch I's public-PyPI 1.1.12 live filter on owned view 52/dataset 36 then
persisted observed task 11, whose exact-parent read reported `executed`; the
bounded preview oracle also confirmed the typed filter predicate. This supports
only the **typed filter path** of REL-461. Raw `view.task.add` still requires an
opaque task specification and remains unsupported as a general user-authored
task payload. No Full claim follows.
