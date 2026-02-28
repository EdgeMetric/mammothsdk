# Pipeline API Reference

The `PipelineAPI` manages the transformation pipeline on dataviews. Each dataview has an ordered list of pipeline tasks (filter, join, pivot, etc.) that transform the data.

**Access**: `client.pipeline`

!!! tip
    Most users should use the high-level `View` transformation methods (e.g. `view.filter_rows()`, `view.math()`) instead of calling `PipelineAPI` directly. The View methods call `PipelineAPI` internally and handle job waiting and metadata refresh automatically.

---

::: mammoth.api.pipeline.PipelineAPI
    options:
      show_root_heading: true
      heading_level: 2
