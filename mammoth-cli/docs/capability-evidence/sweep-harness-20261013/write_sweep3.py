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



code, env = run(["view", "conditional-format", "list", str(V), str(ds)], PROF, P)
rid = env["data"][0]["rule_id"]
step("view.conditional-format.delete-all", ["view", "conditional-format", "delete-all", str(V), str(ds), "--input", J({"rule_id": rid}), "--yes"], note="with rule_id")
step("view.draft.command", ["view", "draft", "command", str(V), "--input", J({"dataset_id": ds, "command": "enter"})], note="enter")
step("view.draft.command", ["view", "draft", "command", str(V), "--input", J({"dataset_id": ds, "command": "discard"}), "--yes", "--confirm", str(V)], note="discard with --yes --confirm")
spec = {"DATAVIEW_ID": V, "handler_type": "csv_file", "trigger_type": "none", "run_immediately": False, "target_properties": {"file": "ev_export", "file_type": "csv", "include_hidden": False}}
ex = step("view.export.create", ["view", "export", "create", str(V), "--input", J({"dataset_id": ds, "export_spec": spec}), "--yes"], note="with run_immediately:false (required; omitting it gives a misleading invalid_input_field_type)")
print("EX", json.dumps(ex)[:300])
exid = str(gid(ex, "id", "export_id") or "0")
step("view.export.get", ["view", "export", "get", str(V), exid], note="read-back")
step("view.export.update", ["view", "export", "update", str(V), exid, "--input", J({"dataset_id": ds, "patches": [{"op": "replace", "path": "params", "value": dict(spec, target_properties={"file": "ev_export2", "file_type": "csv", "include_hidden": False})}]}), "--yes"])
step("view.export.delete", ["view", "export", "delete", str(V), exid, "--input", J({"dataset_id": ds}), "--yes"])
d3 = 88934
code, env = run(["batch", "list", str(d3)], PROF, P)
print("BATCHES", json.dumps(env)[:500])
step("batch.update", ["batch", "update", str(d3), "--input", J({"patch": {"op": "replace", "path": "name", "value": "ev-batch"}})], note="patch as object")
fa = run(["folder", "create", "ev-g1"], PROF, P)[1].get("data") or {}
fb = run(["folder", "create", "ev-g2"], PROF, P)[1].get("data") or {}
print("FOLDERS", json.dumps(fa)[:300])
step("folder.move", ["folder", "move", "--input", J({"resource_ids": [str(fa.get("resource_id") or fa.get("id"))], "target_folder_resource_id": str(fb.get("resource_id") or fb.get("id"))})])
step("folder.bulk-delete", ["folder", "bulk-delete", "--input", J({"folder_ids": [fa["id"], fb["id"]]}), "--yes"])
with open(OUT, "w") as f:
    for r in rows:
        f.write(json.dumps(r, sort_keys=True) + "\n")
