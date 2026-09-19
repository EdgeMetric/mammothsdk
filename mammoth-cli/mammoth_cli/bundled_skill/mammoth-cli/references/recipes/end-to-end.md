# Worked example: three CSVs to a per-region summary

One complete run, in order, with the read-back after every value-changing
step. Ids are placeholders; take each one from the previous command's `data`.
Every command also takes `--profile PROFILE` when the task names one.

```bash
# 0. preflight
mammoth auth status --output json --no-input           # endpoint matches the task's environment
mammoth doctor --output json --no-input                # must succeed
mammoth project list --output json --no-input          # baseline: ids that exist before you start

# 1. own project, upload, find the view ids
mammoth project ensure 'From Claude' --output json --no-input                # -> PROJECT_ID (data.project_id; reused next time)
mammoth file upload orders.csv --project PROJECT_ID --output json --no-input # -> data.datasets[].id/status
mammoth file upload customers.csv --project PROJECT_ID --output json --no-input
# a dataset in need_action is not usable yet: follow need-action.md (file-settings update), then re-read
mammoth dataset list --project PROJECT_ID --output json --no-input
mammoth view list ORDERS_DS --project PROJECT_ID --output json --no-input    # -> ORDERS_VIEW
mammoth view list CUSTOMERS_DS --project PROJECT_ID --output json --no-input # -> CUSTOMERS_VIEW

# 2. look before you change: column names, types, row_count, a sample
mammoth view get ORDERS_VIEW ORDERS_DS --project PROJECT_ID --output json --no-input
mammoth view data get ORDERS_VIEW ORDERS_DS --project PROJECT_ID --output json --no-input

# 3. clean orders (each call waits for its job; read back after each value change)
mammoth view transform discard-duplicates ORDERS_VIEW --project PROJECT_ID \
  --input '{"dataset_id": ORDERS_DS}' --output json --no-input
mammoth view transform bulk-replace ORDERS_VIEW --project PROJECT_ID \
  --input '{"dataset_id": ORDERS_DS, "columns": ["amount"], "mapping": [{"search": ["$", ","], "replace": ""}]}' --output json --no-input
mammoth view transform convert-type ORDERS_VIEW --project PROJECT_ID \
  --input '{"dataset_id": ORDERS_DS, "conversions": [{"column": "amount", "to": "NUMERIC"}, {"column": "order_date", "to": "DATE"}]}' --output json --no-input
mammoth view transform set-values ORDERS_VIEW --project PROJECT_ID \
  --input '{"dataset_id": ORDERS_DS, "existing_column": "amount", "values": [{"value": 0}], "condition": {"column": "amount", "operator": "IS_EMPTY"}}' --output json --no-input
mammoth view data get ORDERS_VIEW ORDERS_DS --project PROJECT_ID --output json --no-input
#   invariant: only rows whose amount was blank are now 0; every other amount is unchanged
mammoth view transform filter ORDERS_VIEW --project PROJECT_ID \
  --input '{"dataset_id": ORDERS_DS, "condition": {"column": "qty", "operator": "LT", "value": 0}, "filter_type": "REMOVE"}' --output json --no-input
mammoth view get ORDERS_VIEW ORDERS_DS --project PROJECT_ID --output json --no-input   # row_count before vs after; state both

# 4. clean customers the same way (text trim/case, set-values for blanks), read back

# 5. join, then check the match rate before building on it
mammoth view transform join ORDERS_VIEW --project PROJECT_ID \
  --input '{"dataset_id": ORDERS_DS, "foreign_view": CUSTOMERS_VIEW, "foreign_dataset_id": CUSTOMERS_DS, "join_type": "LEFT", "on": [{"left": "customer_id", "right": "customer_id"}], "select": ["region"]}' --output json --no-input
mammoth view data get ORDERS_VIEW ORDERS_DS --project PROJECT_ID --output json --no-input
#   if region is empty/"Unknown" on most rows, the key does not match: compare the two key columns' values
#   (type, padding, case) with view data get on both views; do not summarise unmatched data

# 6. deliverable first: export the cleaned, joined rows before any step that replaces them
mammoth view export csv ORDERS_VIEW --project PROJECT_ID \
  --input '{"dataset_id": ORDERS_DS, "output_path": "orders_clean.csv"}' --output json --no-input
#   check the file's header and row count against the last readback

# 7. per-region summary as the LAST step on the same view (pivot replaces the view's columns in place;
#    do not use view create with clone_from for this: on release the clone job succeeds but the copy
#    answers every read with 4DTVW019 and its copied tasks never execute)
mammoth view transform pivot ORDERS_VIEW --project PROJECT_ID \
  --input '{"dataset_id": ORDERS_DS, "group_by": ["region"], "aggregations": [{"column": "amount", "function": "SUM", "as_name": "total_amount"}, {"column": "order_id", "function": "COUNT", "as_name": "order_count"}]}' --output json --no-input
mammoth view data get ORDERS_VIEW ORDERS_DS --project PROJECT_ID --output json --no-input
#   Σ order_count over groups == the cleaned row count; no group's total_amount is 0 unless its rows really are
mammoth view export csv ORDERS_VIEW --project PROJECT_ID \
  --input '{"dataset_id": ORDERS_DS, "output_path": "orders_by_region.csv"}' --output json --no-input

# 8. cleanup only what you created, one id per call, read back
mammoth dataset delete INTERMEDIATE_DS --project PROJECT_ID --output json --no-input --yes
mammoth dataset list --project PROJECT_ID --output json --no-input           # the id is gone
mammoth project list --output json --no-input                                # matches the baseline plus your deliverables
# only if the task said the whole project was temporary:
# mammoth project delete PROJECT_ID --output json --no-input --yes --confirm PROJECT_ID
```

Then walk the [report checklist](../report-checklist.md). If any step
returned exit 7 or `outcome_unknown`, reconcile it (re-read the view's
`view task list`) before deciding whether to replay.
