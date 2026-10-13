"""Live sweep of every `view transform` command on koyal (project 25654, own fixtures).

Each transform runs once on its own fresh view cloned from the fixture dataset,
then is read back with `view data get` against a known answer.
"""

import json
import sys

from sweeplib import run

P, PROF = 25654, "koyal"
DS_FIX, DS_A, DS_B, VIEW_B = 88928, 88929, 88930, 88928
OUT = sys.argv[1]
created = {"views": [], "datasets": []}


def mkview(ds=DS_FIX, name="ev"):
    c, e = run(
        ["view", "create", str(ds), "--input", json.dumps({"name": name})], PROF, P
    )
    vid = e["data"]["id"]
    created["views"].append(vid)
    return vid


def rows(vid):
    c, e = run(["view", "data", "get", str(vid)], PROF, P)
    return e.get("data", {}).get("data", []), e


def col(r, i):
    return r[i] if i < len(r) else None


def by_id(rs):
    return {x.get("id"): x for x in rs}


def types(resp):
    return {c["name"]: c["type"] for c in resp["data"]["state"]["columns"]}


# name -> (input, check(rows_by_id, response, all_rows) -> observed dict or None on failure)
def T(name, inp, check, ds=DS_FIX):
    return name, inp, check, ds


def want(obs, exp):
    return obs if obs == exp else None


CASES = [
    T(
        "convert-type",
        {
            "conversions": [
                {"column": "amount", "to": "NUMERIC"},
                {"column": "id", "to": "TEXT"},
            ]
        },
        lambda b, r, a: (
            lambda t: (
                {"id": t["id"], "skipped": r["data"].get("skipped")}
                if t["id"] == "TEXT" and r["data"].get("skipped")
                else None
            )
        )(types(r)),
    ),
    T(
        "add-column",
        {"column_type": "TEXT", "name": "note"},
        lambda b, r, a: (
            {"note": types(r).get("note")} if types(r).get("note") == "TEXT" else None
        ),
    ),
    T(
        "set-values",
        {
            "condition": {"column": "status", "operator": "IS_EMPTY"},
            "existing_column": "status",
            "values": [{"value": "unknown"}],
        },
        lambda b, r, a: want(
            {"1": b["1"]["status"], "2": b["2"]["status"]},
            {"1": "active", "2": "unknown"},
        ),
    ),
    T(
        "math",
        {"expression": "amount * qty", "new_column": "total"},
        lambda b, r, a: want(
            {"1": b["1"]["total"], "2": b["2"]["total"]}, {"1": "21", "2": "20"}
        ),
    ),
    T(
        "text",
        {"case": "UPPER", "columns": ["name"], "trim": True},
        lambda b, r, a: want({"1": b["1"]["name"]}, {"1": "ALICE SMITH"}),
    ),
    T(
        "replace",
        {"columns": ["city"], "find": "boston", "replace": "Boston"},
        lambda b, r, a: want(
            {"1": b["1"]["city"], "2": b["2"]["city"]}, {"1": "Boston", "2": "austin"}
        ),
    ),
    T(
        "bulk-replace",
        {
            "columns": ["city"],
            "mapping": [
                {"replace": "Austin", "search": ["austin"]},
                {"replace": "Denver", "search": ["denver"]},
            ],
        },
        lambda b, r, a: want(
            {"2": b["2"]["city"], "4": b["4"]["city"]}, {"2": "Austin", "4": "Denver"}
        ),
    ),
    T(
        "combine-columns",
        {"new_column": "city_status", "separator": "-", "sources": ["city", "status"]},
        lambda b, r, a: want({"1": b["1"]["city_status"]}, {"1": "boston-active"}),
    ),
    T(
        "copy-columns",
        {"copies": [{"as_name": "amount_copy", "source": "amount", "type": "NUMERIC"}]},
        lambda b, r, a: want({"1": b["1"]["amount_copy"]}, {"1": "10.5"}),
    ),
    T(
        "substring",
        {"column": "code", "direction": "START", "new_column": "prefix", "num_char": 2},
        lambda b, r, a: want({"3": b["3"]["prefix"]}, {"3": "EF"}),
    ),
    T(
        "split",
        {
            "column": "tags",
            "delimiter": "|",
            "new_columns": [{"name": "tag1"}, {"name": "tag2"}],
        },
        lambda b, r, a: want(
            {"tag1": b["1"]["tag1"], "tag2": b["1"]["tag2"]},
            {"tag1": "red", "tag2": "blue"},
        ),
    ),
    T(
        "json-extract",
        {"column": "payload", "keep_source": True, "keys": ["k"]},
        lambda b, r, a: want({"k": b["3"]["k"]}, {"k": "c"}),
    ),
    T(
        "extract-date",
        {"column": "start_date", "component": "month", "new_column": "start_month"},
        lambda b, r, a: want({"3": b["3"]["start_month"]}, {"3": "3"}),
    ),
    T(
        "date-diff",
        {
            "component": "DAY",
            "end": "end_date",
            "new_column": "days",
            "start": "start_date",
        },
        lambda b, r, a: want(
            {"1": b["1"]["days"], "4": b["4"]["days"]}, {"1": "10", "4": "30"}
        ),
    ),
    T(
        "increment-date",
        {"column": "start_date", "delta": {"days": 30}, "new_column": "due"},
        lambda b, r, a: want({"1": b["1"]["due"]}, {"1": "31-Jan-2026"}),
    ),
    T(
        "small-large",
        {"columns": ["q1", "q2"], "function": "LARGE", "new_column": "qmax"},
        lambda b, r, a: want(
            {"1": b["1"]["qmax"], "2": b["2"]["qmax"]}, {"1": "7", "2": "9"}
        ),
    ),
    T(
        "window",
        {
            "column": "amount",
            "function": "SUM",
            "new_column": "city_total",
            "partition_by": ["city"],
        },
        lambda b, r, a: want({"1": b["1"]["city_total"]}, {"1": "30.5"}),
    ),
    T(
        "fill-missing",
        {"column": "score", "direction": "LAST_VALUE", "order_by": [["id", "ASC"]]},
        lambda b, r, a: want(
            {"2": b["2"]["score"], "4": b["4"]["score"]}, {"2": "5", "4": "8"}
        ),
    ),
    T(
        "delete-columns",
        {"columns": ["code"]},
        lambda b, r, a: (
            {"has_code": "code" in b["1"], "columns": len(b["1"])}
            if "code" not in b["1"]
            else None
        ),
    ),
    T(
        "rename-columns",
        {"renames": {"city": "City"}},
        lambda b, r, a: (
            {"has": "City"} if "City" in b["1"] and "city" not in b["1"] else None
        ),
    ),
    T(
        "sort",
        {"order_by": [["amount", "DESC"]]},
        lambda b, r, a: (
            {"first_amount": a[0]["amount"]} if a[0]["amount"] == "20" else None
        ),
    ),
    T(
        "discard-duplicates",
        {},
        lambda b, r, a: {"rows": len(a)} if len(a) == 6 else None,
    ),
    T(
        "filter",
        {
            "condition": {"column": "amount", "operator": "GT", "value": 3.5},
            "filter_type": "SHOW",
        },
        lambda b, r, a: {"rows": len(a)} if len(a) == 5 else None,
    ),
    T(
        "limit-rows",
        {"n": 2, "order_by": [["amount", "DESC"]]},
        lambda b, r, a: (
            {"amounts": [x["amount"] for x in a], "rows": len(a)}
            if [x["amount"] for x in a] == ["20", "12"]
            else None
        ),
    ),
    T(
        "pivot",
        {
            "aggregations": [
                {"as_name": "orders", "column": "id", "function": "COUNT"}
            ],
            "group_by": ["city"],
        },
        lambda b, r, a: (
            {"cols": list(a[0].keys()), "rows": len(a)}
            if len(a) == 3 and set(a[0]) == {"city", "orders"}
            else None
        ),
    ),
    T(
        "unnest",
        {"columns": ["q1", "q2"], "label_column": "Quarter", "value_column": "Value"},
        lambda b, r, a: {"rows": len(a)} if len(a) == 14 else None,
    ),
    T(
        "first-name",
        {"column": "name", "new_column": "first"},
        lambda b, r, a: want(
            {"1": b["1"]["first"], "3": b["3"]["first"]}, {"1": "alice", "3": "carol"}
        ),
    ),
    T(
        "update-column",
        {"column": "amount", "expression": "amount + 5"},
        lambda b, r, a: want(
            {"1": b["1"]["amount"], "2": b["2"]["amount"]}, {"1": "15.5", "2": "9"}
        ),
    ),
    T(
        "lookup",
        {
            "key": "id",
            "lookup_dataset_id": DS_B,
            "lookup_view_id": VIEW_B,
            "new_column": "cust_name",
            "source": "cust_ref",
            "value": "name",
        },
        lambda b, r, a: (
            {"O0001": a[0].get("cust_name")}
            if a[0].get("order_id") == "O0001" and a[0].get("cust_name") == "Fjord AS"
            else None
        ),
        ds=DS_A,
    ),
    T(
        "join",
        {
            "foreign_dataset_id": DS_B,
            "foreign_view": VIEW_B,
            "join_type": "LEFT",
            "on": [{"left": "cust_ref", "right": "id"}],
            "select": ["segment"],
        },
        lambda b, r, a: (
            {"rows": len(a)} if len(a) == 40 and "segment" in a[0] else None
        ),
        ds=DS_A,
    ),
    T(
        "add-sql",
        {"query": 'SELECT city, COUNT(*) AS n FROM "view:{VID}" GROUP BY city'},
        lambda b, r, a: (
            {"cols": list(a[0].keys()), "rows": len(a)}
            if len(a) == 3 and set(a[0]) == {"city", "n"}
            else None
        ),
    ),
    T(
        "crosstab",
        {
            "dataset_name": "ev_sweep_xtab_1013",
            "pivot_column": "status",
            "rows": ["city"],
            "select": {"function": "COUNT"},
        },
        lambda b, r, a: {"dataset": "ev_sweep_xtab_1013"} if r["data"] else None,
    ),
    T(
        "generate-sql",
        {"intent": "Count the rows for each city"},
        lambda b, r, a: (
            {"applied": r["data"].get("applied")}
            if r["data"].get("applied") is False
            else None
        ),
    ),
    T(
        "ai",
        {
            "context_columns": ["city"],
            "new_column": "vibe",
            "prompt": "In one word, describe this city",
        },
        lambda b, r, a: (
            {"filled": sum(1 for x in a if x.get("vibe"))}
            if sum(1 for x in a if x.get("vibe")) >= 3
            else None
        ),
    ),
]

res = []
for name, inp, check, ds in CASES:
    vid = mkview(ds, "ev-" + name)
    inp = json.loads(json.dumps(inp).replace("{VID}", str(vid)))
    argv = ["view", "transform", name, str(vid), "--input", json.dumps(inp)]
    code, env = run(argv, PROF, P, timeout=240)
    row = {
        "command": f"view transform {name}",
        "view_id": vid,
        "dataset_id": ds,
        "input": inp,
        "exit": code,
    }
    if code != 0 or "error" in env:
        e = env.get("error", {})
        row.update(
            ok=False,
            observed=None,
            note=f"{e.get('code')}: {(e.get('message') or '')[:200]} {(e.get('details') or {}).get('status_code') or ''}",
        )
    else:
        try:
            if name == "crosstab":
                a, _ = [], None
                b = {}
            else:
                a, _ = rows(vid)
                b = by_id(a)
            obs = check(b, env, a)
            row.update(
                ok=obs is not None,
                observed=obs,
                note=(
                    None
                    if obs is not None
                    else "read-back did not match the known answer"
                ),
            )
        except Exception as ex:
            row.update(
                ok=False,
                observed=None,
                note=f"read-back raised {type(ex).__name__}: {ex}",
            )
    res.append(row)
    print(name, row["ok"], row.get("note"), flush=True)
with open(OUT, "w") as f:
    for r in res:
        f.write(json.dumps(r, sort_keys=True) + "\n")
json.dump(created, open("/tmp/claude-1000/out/created_transform.json", "w"))
