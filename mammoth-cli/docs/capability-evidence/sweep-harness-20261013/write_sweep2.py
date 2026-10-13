"""Second pass of the write sweep: commands whose first-pass input was wrong in the harness (not in the CLI)."""

import json
import sys

from sweeplib import classify, run

P, PROF = 25654, "koyal"
ds, V = 88932, 88936
OUT = sys.argv[1]
rows = []


def J(x):
    return json.dumps(x)


def step(cid, argv, note=None, ok=None):
    code, env = run(argv, PROF, P, timeout=240)
    v, info = classify(code, env)
    row = {
        "command_id": cid,
        "argv": " ".join(argv)[:300],
        "exit": code,
        "verdict": v,
        **info,
    }
    if note:
        row["note"] = note
    if v in ("ok", "ok_empty") and ok is not None:
        try:
            if not ok(env.get("data")):
                row["verdict"] = "fail_readback"
        except Exception as ex:
            row["verdict"] = "fail_readback"
            row["note"] = f"readback raised {type(ex).__name__}: {ex}"
    rows.append(row)
    print(cid, row["verdict"], row.get("backend_message", "")[:160], flush=True)
    return env.get("data") if code == 0 else None


def gid(d, *keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k) is not None:
            return d[k]
    return None


cp = step(
    "view.checkpoint.create",
    [
        "view",
        "checkpoint",
        "create",
        str(V),
        str(ds),
        "--input",
        J(
            {
                "body": {
                    "checkpoint_name": "ev-cp",
                    "checkpoint_type": "alert",
                    "pinned_to_end": True,
                }
            }
        ),
    ],
)
print("CP", json.dumps(cp)[:300])
code, env = run(["view", "checkpoint", "list", str(V), str(ds)], PROF, P)
print("CPLIST", json.dumps(env)[:400])
cpid = str(gid(cp, "id", "checkpoint_id") or "")
if not cpid:
    items = (
        next((v for v in (env.get("data") or {}).values() if isinstance(v, list)), [])
        if isinstance(env.get("data"), dict)
        else (env.get("data") or [])
    )
    cpid = str(items[-1]["id"]) if items else "0"
step(
    "view.checkpoint.get",
    ["view", "checkpoint", "get", str(V), cpid, str(ds)],
    ok=lambda d: bool(d),
)
step(
    "view.checkpoint.update",
    [
        "view",
        "checkpoint",
        "update",
        str(V),
        cpid,
        str(ds),
        "--input",
        J({"body": {"patches": [{"op": "command", "path": "approve", "value": None}]}}),
    ],
)
step(
    "view.checkpoint.delete",
    ["view", "checkpoint", "delete", str(V), cpid, str(ds), "--yes"],
)
code, env = run(["view", "checkpoint", "list", str(V), str(ds)], PROF, P)
print("CPLIST after delete", json.dumps(env)[:300])

dc = step(
    "view.data-check.create",
    [
        "view",
        "data-check",
        "create",
        str(V),
        str(ds),
        "--input",
        J(
            {
                "body": {
                    "name": "ev-dc",
                    "pinned_to_end": True,
                    "checks": [
                        {
                            "check_type": "null_percentage",
                            "config": {
                                "column": "status",
                                "condition": "lt",
                                "threshold": 50.0,
                            },
                        }
                    ],
                }
            }
        ),
    ],
)
print("DC", json.dumps(dc)[:300])
dcid = str(gid(dc, "id", "data_check_id") or "0")
step(
    "view.data-check.get",
    ["view", "data-check", "get", str(V), dcid, str(ds)],
    ok=lambda d: bool(d),
)
step(
    "view.data-check.update",
    [
        "view",
        "data-check",
        "update",
        str(V),
        dcid,
        str(ds),
        "--input",
        J({"body": {"patches": [{"op": "command", "path": "disable", "value": None}]}}),
    ],
)
step(
    "view.data-check.delete",
    ["view", "data-check", "delete", str(V), dcid, str(ds), "--yes"],
)

cf = step(
    "view.conditional-format.create",
    [
        "view",
        "conditional-format",
        "create",
        str(V),
        str(ds),
        "--input",
        J({"columns": ["amount"], "operator": "<", "value": 5, "color": "red"}),
    ],
)
print("CF", json.dumps(cf)[:400])
code, env = run(["view", "conditional-format", "list", str(V), str(ds)], PROF, P)
print("CFLIST", json.dumps(env)[:400])

with open(OUT, "w") as f:
    for r in rows:
        f.write(json.dumps(r, sort_keys=True) + "\n")
