# Enums & Data Classes Reference

The SDK provides enums for all transformation parameters. Import them directly from `mammoth`:

```python
from mammoth import Operator, ColumnType, JoinType, DateComponent
```

All enums are `str` subclasses (`class MyEnum(str, Enum)`) so they can be used directly as strings where needed.

---

## Enums

::: mammoth.models.pipeline.Operator

::: mammoth.models.pipeline.ColumnType

::: mammoth.models.pipeline.FilterType

::: mammoth.models.pipeline.JoinType

::: mammoth.models.pipeline.TextCase

::: mammoth.models.pipeline.DateComponent

::: mammoth.models.pipeline.DateDiffUnit

::: mammoth.models.pipeline.AggregateFunction

::: mammoth.models.pipeline.WindowFunction

::: mammoth.models.pipeline.WindowRange

::: mammoth.models.pipeline.FillDirection

::: mammoth.models.pipeline.SortDirection

::: mammoth.models.pipeline.MathOperator

::: mammoth.models.pipeline.SubstringDirection

::: mammoth.models.pipeline.JsonType

::: mammoth.models.pipeline.JsonOpType

::: mammoth.models.pipeline.ExportFileType

::: mammoth.models.pipeline.ProviderType

::: mammoth.models.pipeline.TaskType

::: mammoth.models.pipeline.DraftCommand

---

## Data Classes

::: mammoth.models.pipeline.SetValue

::: mammoth.models.pipeline.CopySpec

::: mammoth.models.pipeline.ConversionSpec

::: mammoth.models.pipeline.SplitColumnSpec

::: mammoth.models.pipeline.BulkReplaceMapping

::: mammoth.models.pipeline.DateDelta

::: mammoth.models.pipeline.AggregationSpec

::: mammoth.models.pipeline.JoinKeySpec

::: mammoth.models.pipeline.JoinSelectSpec

::: mammoth.models.pipeline.JsonExtractionSpec

::: mammoth.models.pipeline.CrosstabSpec

## See also

- [Conditions](conditions.md) -- how to use Operator with Condition
- [Views](views.md) -- transformation methods that use these enums
