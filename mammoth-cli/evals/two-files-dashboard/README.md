# Agent eval: two files, one dashboard

A cold agent gets one sentence from a business user: "I have two files, t_a
and t_b. Create a dashboard from them in Mammoth." Nothing tells it how the
files relate or what is wrong with them. Run this before every CLI release,
with a small model (Haiku), on the release environment.

## The data (synthetic)

- `data/t_a.csv`: 40 orders (`order_id, cust_ref, order_date, product, qty,
  price`).
- `data/t_b.csv`: 8 customers (`id, name, city, segment`).

Built-in traps:

- The key is not named: `t_a.cust_ref` holds `t_b.id` values.
- `price` is TEXT: 36 numbers, 3 `N/A`, 1 blank.
- `qty` has 1 blank; `segment` has 2 blanks.
- Order `O0017` has `cust_ref` `C099`, which is not in `t_b` (1 unmatched row).

## How to run

1. Fill in `BRIEF.md`: `EVAL_DIR` is this folder, `WORK_DIR` a scratch folder,
   `VERSION_UNDER_TEST` the version just published.
2. Give the filled brief to a fresh agent with shell access and nothing else
   (no repository, no chat context). The `release` profile must hold a
   credential for release workspace 4.
3. Grade its report against the checklist below. Record the result in
   `docs/release-status.md` under the release.

## Checklist

| # | Check | Pass when the report shows |
|---|---|---|
| 1 | Version | `mammoth --version` equals the version under test |
| 2 | Inspect in Mammoth | `view get` / `view data get` on both views before any change |
| 3 | Key found | a join or lookup on `cust_ref` = `id`, found from the data |
| 4 | Match rate | 39 of 40 matched; `C099` named as unmatched |
| 5 | Price fixed | `price` converted to NUMERIC before the dashboard; `N/A` handled and said |
| 6 | Blanks decided | `qty` and `segment` blanks filled, filtered, or kept and said |
| 7 | Dashboard has data | a dashboard on the joined view; a number read back (for example 40 orders) |
| 8 | Money on the dashboard | a revenue or price measure (possible only after check 5) |
| 9 | CLI only | no browser, no REST/SDK calls, no local computation |
| 10 | Cleanup | the project is deleted and reads back as not found |

A run passes with all ten. Checks 4 to 6 fail when an agent builds
without reading the CLI's `column_warnings` and `join_check` output.

## History

| CLI | Result | Misses |
|---|---|---|
| 2.0.37 | 5 of 10 | 2 (read local files), 4, 5, 6, 8 |
| 2.0.38 | 7 of 10 | 5, 6, 8 (saw the problems, did not fix them) |
| 2.0.39 | 8 of 10 | 6 (`qty` blank seen, not decided), 8 (converted `price`, but charted only `qty`) |

2.0.39 notes: the agent acted on `column_warnings` (converted `price`) and
reported `join_check` (39 of 40, `C099`). New friction: `dashboard pages add`
with a chart the data does not support (`pie`, `vbar`, a date as `dim`)
still adds the page, so the dashboard kept two empty pages. A first run
that could not find 2.0.39 on the index installed 2.0.38; it was discarded,
and the brief now forbids another version.
