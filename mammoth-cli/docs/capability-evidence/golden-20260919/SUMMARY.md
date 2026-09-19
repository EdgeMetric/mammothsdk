# Golden-data check (20260919-122317)

Profile `release`, owned project 40. Every value-changing transform was read back with `view data get` and its values compared with the known answer for the fixture; see `results.jsonl` for each command.

## Assertions

- OK   upload orders.csv reached ready (got ready)
- OK   upload customers.csv reached ready (got ready)
- OK   orders upload has 6 rows (got 6)
- OK   amount is text with a USD prefix before bulk-replace
- OK   bulk-replace: 1234.56
- OK   bulk-replace: 7000
- OK   bulk-replace left status untouched
- OK   convert-type: amount numeric 1234.56
- OK   convert-type: blank stays null
- OK   set-values: blank -> 0
- OK   set-values: non-blank amounts unchanged
- OK   text: statuses ['active', 'inactive']
- OK   filter: remaining order ids ['1', '2', '3', '5']
- OK   discard-duplicates: 6 -> 5 rows (got 5)
- OK   join keeps 4 rows (got 4)
- OK   join: order 1 -> north
- OK   join: order 2 -> south
- OK   join: unmatched C9 -> null region
- OK   export csv rows == readback rows (4)
- OK   export csv carries the joined region column
- OK   pivot: Σ order_count == 4 (got 4)
- OK   pivot: north total 1234.56
- OK   pivot: south total 10 (0 + 10)
- OK   project 40 gone after delete

## Verdict

All assertions held.
