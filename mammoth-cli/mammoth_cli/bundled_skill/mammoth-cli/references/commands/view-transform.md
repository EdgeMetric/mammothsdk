# `view-transform` commands

Every command returns the standard JSON envelope. On nonzero exit, read the error envelope and its `recovery_commands`; do not guess request fields. "Status on release" is joined from `docs/release-capability-matrix.json`: *ran once* means one bounded live run succeeded on the named CLI release, *untried* means nobody has run it, *not supported* means the backend refuses it. When this file disagrees with [capabilities](../capabilities.md) or a recipe, they win. Envelope shapes: [machine output](../machine-output.md).

### `view.transform.add-column`

Run: `mammoth view transform add-column`. Exact input fields: `mammoth schema get view.transform.add-column`.

Example: `mammoth view transform add-column 123 --input '{"name": "Revenue report", "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformAddColumnResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.add-sql`

Run: `mammoth view transform add-sql`. Exact input fields: `mammoth schema get view.transform.add-sql`.

Example: `mammoth view transform add-sql 123 --input '{"query": "SELECT region, SUM(revenue) AS revenue FROM \"view:123\" GROUP BY region", "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformAddSqlResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.ai`

Run: `mammoth view transform ai`. Exact input fields: `mammoth schema get view.transform.ai`.

Example: `mammoth view transform ai 123 --input '{"prompt": "Summarize revenue by region", "context_columns": ["Status"], "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformAiResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.bulk-replace`

Run: `mammoth view transform bulk-replace`. Exact input fields: `mammoth schema get view.transform.bulk-replace`.

Example: `mammoth view transform bulk-replace 123 --input '{"columns": ["Status"], "mapping": [{"search": ["sample"], "replace": "sample"}], "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformBulkReplaceResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.combine-columns`

Run: `mammoth view transform combine-columns`. Exact input fields: `mammoth schema get view.transform.combine-columns`.

Example: `mammoth view transform combine-columns 123 --input '{"sources": ["Status"], "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformCombineColumnsResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.convert-type`

Run: `mammoth view transform convert-type`. Exact input fields: `mammoth schema get view.transform.convert-type`.

Example: `mammoth view transform convert-type 123 --input '{"conversions": [{"column": "Status", "to": "TEXT"}], "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformConvertTypeResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.copy-columns`

Run: `mammoth view transform copy-columns`. Exact input fields: `mammoth schema get view.transform.copy-columns`.

Example: `mammoth view transform copy-columns 123 --input '{"copies": [{"source": "Status"}], "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformCopyColumnsResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.crosstab`

Run: `mammoth view transform crosstab`. Exact input fields: `mammoth schema get view.transform.crosstab`.

Example: `mammoth view transform crosstab 123 --input '{"rows": ["sample"], "pivot_column": "Status", "select": {"function": "SUM"}, "dataset_name": "Revenue report", "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformCrosstabResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.date-diff`

Run: `mammoth view transform date-diff`. Exact input fields: `mammoth schema get view.transform.date-diff`.

Example: `mammoth view transform date-diff 123 --input '{"component": "YEAR", "start": "sample", "end": "sample", "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformDateDiffResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.delete-columns`

Run: `mammoth view transform delete-columns`. Exact input fields: `mammoth schema get view.transform.delete-columns`.

Example: `mammoth view transform delete-columns 123 --input '{"columns": ["Status"], "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformDeleteColumnsResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.discard-duplicates`

Run: `mammoth view transform discard-duplicates`. Exact input fields: `mammoth schema get view.transform.discard-duplicates`.

Example: `mammoth view transform discard-duplicates 123 --input '{"dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformDiscardDuplicatesResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.extract-date`

Run: `mammoth view transform extract-date`. Exact input fields: `mammoth schema get view.transform.extract-date`.

Example: `mammoth view transform extract-date 123 --input '{"column": "Status", "component": "year", "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformExtractDateResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.fill-missing`

Run: `mammoth view transform fill-missing`. Exact input fields: `mammoth schema get view.transform.fill-missing`.

Example: `mammoth view transform fill-missing 123 --input '{"column": "Status", "direction": "FIRST_VALUE", "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformFillMissingResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.filter`

Run: `mammoth view transform filter`. Exact input fields: `mammoth schema get view.transform.filter`.

Example: `mammoth view transform filter 123 --input '{"condition": {"column": "Status", "operator": "EQ", "value": "Active"}, "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformFilterResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.generate-sql`

Run: `mammoth view transform generate-sql`. Exact input fields: `mammoth schema get view.transform.generate-sql`.

Example: `mammoth view transform generate-sql 123 --input '{"intent": "Summarize revenue by region", "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformGenerateSqlResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.increment-date`

Run: `mammoth view transform increment-date`. Exact input fields: `mammoth schema get view.transform.increment-date`.

Example: `mammoth view transform increment-date 123 --input '{"column": "Status", "delta": {}, "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformIncrementDateResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.join`

Run: `mammoth view transform join`. Exact input fields: `mammoth schema get view.transform.join`.

Example: `mammoth view transform join 123 --input '{"foreign_view": 1, "join_type": "INNER", "on": [{"left": "sample", "right": "sample"}], "select": ["sample"], "dataset_id": 456, "foreign_dataset_id": 457}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformJoinResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.json-extract`

Run: `mammoth view transform json-extract`. Exact input fields: `mammoth schema get view.transform.json-extract`.

Example: `mammoth view transform json-extract 123 --input '{"column": "Status", "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformJsonExtractResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.limit-rows`

Run: `mammoth view transform limit-rows`. Exact input fields: `mammoth schema get view.transform.limit-rows`.

Example: `mammoth view transform limit-rows 123 --input '{"n": 1, "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformLimitRowsResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.lookup`

Run: `mammoth view transform lookup`. Exact input fields: `mammoth schema get view.transform.lookup`.

Example: `mammoth view transform lookup 123 --input '{"source": "Status", "lookup_view_id": 1, "key": "Status", "value": "sample", "dataset_id": 456, "lookup_dataset_id": 457}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformLookupResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.math`

Run: `mammoth view transform math`. Exact input fields: `mammoth schema get view.transform.math`.

Example: `mammoth view transform math 123 --input '{"expression": "price * quantity", "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformMathResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.pivot`

Run: `mammoth view transform pivot`. Exact input fields: `mammoth schema get view.transform.pivot`.

Example: `mammoth view transform pivot 123 --input '{"group_by": ["sample"], "aggregations": [{"column": "Status", "function": "SUM"}], "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformPivotResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.rename-columns`

Run: `mammoth view transform rename-columns`. Exact input fields: `mammoth schema get view.transform.rename-columns`.

Example: `mammoth view transform rename-columns 123 --input '{"renames": {"cust_id": "Customer ID"}, "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformRenameColumnsResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.replace`

Run: `mammoth view transform replace`. Exact input fields: `mammoth schema get view.transform.replace`.

Example: `mammoth view transform replace 123 --input '{"columns": ["Status"], "find": "sample", "replace": "sample", "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformReplaceResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.set-values`

Run: `mammoth view transform set-values`. Exact input fields: `mammoth schema get view.transform.set-values`.

Example: `mammoth view transform set-values 123 --input '{"values": [{"value": "sample"}], "existing_column": "Status", "condition": {"column": "Status", "operator": "IS_EMPTY"}, "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformSetValuesResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.small-large`

Run: `mammoth view transform small-large`. Exact input fields: `mammoth schema get view.transform.small-large`.

Example: `mammoth view transform small-large 123 --input '{"function": "SMALL", "columns": ["Status"], "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformSmallLargeResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.sort`

Run: `mammoth view transform sort`. Exact input fields: `mammoth schema get view.transform.sort`.

Example: `mammoth view transform sort 123 --input '{"order_by": [["Revenue", "DESC"]], "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformSortResult`; mutation `benign_mutation`, confirmation `none`, wait policy `not_async`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.split`

Run: `mammoth view transform split`. Exact input fields: `mammoth schema get view.transform.split`.

Example: `mammoth view transform split 123 --input '{"column": "Status", "delimiter": "sample", "new_columns": [{"name": "Revenue report"}], "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformSplitResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.substring`

Run: `mammoth view transform substring`. Exact input fields: `mammoth schema get view.transform.substring`.

Example: `mammoth view transform substring 123 --input '{"column": "Status", "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformSubstringResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.text`

Run: `mammoth view transform text`. Exact input fields: `mammoth schema get view.transform.text`.

Example: `mammoth view transform text 123 --input '{"columns": ["Status"], "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformTextResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.unnest`

Run: `mammoth view transform unnest`. Exact input fields: `mammoth schema get view.transform.unnest`.

Example: `mammoth view transform unnest 123 --input '{"columns": ["Status"], "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformUnnestResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.

### `view.transform.window`

Run: `mammoth view transform window`. Exact input fields: `mammoth schema get view.transform.window`.

Example: `mammoth view transform window 123 --input '{"function": "ROW_NUMBER", "dataset_id": 456}'`. Placeholders are illustrative; resolve IDs and input from observed reads.

Result: `ViewTransformWindowResult`; mutation `reversible_pipeline`, confirmation `none`, wait policy `always_wait`.

Status on release: ran once on CLI 2.0.40 through `view.task.add` and was read back with `view data get`; other inputs for this transform are untried.
