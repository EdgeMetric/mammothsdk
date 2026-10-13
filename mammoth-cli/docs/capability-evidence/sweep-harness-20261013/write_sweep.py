"""Write sweep on koyal, project 25654, own fixtures only. Each command once, verdict by observed result.

usage: write_sweep.py OUT.jsonl
"""

import json
import sys

from sweeplib import classify, run

P, PROF = 25654, "koyal"
FIX = "/tmp/claude-1000/ev1013/mammoth-cli/docs/capability-evidence/transform-sweep-20260925/fixture.csv"
OUT = sys.argv[1]
rows = []
created = {"datasets": [], "views": [], "files": [], "folders": []}


def J(x):
    return json.dumps(x)


def step(cid, argv, ok=None, note=None, capture=None, timeout=240):
    code, env = run(
        argv + ["--yes"] if "--yes" in ("",) else argv, PROF, P, timeout=timeout
    )
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
                row["note"] = (
                    note or ""
                ) + " result did not match the expected readback"
        except Exception as ex:
            row["verdict"] = "fail_readback"
            row["note"] = f"readback raised {type(ex).__name__}: {ex}"
    rows.append(row)
    print(cid, row["verdict"], row.get("backend_message", "")[:100], flush=True)
    return env.get("data") if code == 0 else None


def upload(path):
    d = step("file.upload", ["file", "upload", path])
    ds = d["dataset_id"]
    created["datasets"].append(ds)
    code, env = run(["view", "list"], PROF, P)
    vid = max(v["id"] for v in env["data"]["dataviews"] if v["dataset_id"] == ds)
    return ds, vid


before = {f["id"] for f in (run(["file", "list"], PROF, P)[1].get("data") or {}).get("files", [])}
ds, vid = upload(FIX)
ds2, vid2 = upload(FIX)
ds3, vid3 = upload(FIX)
D, V = str(ds), str(vid)

# --- checkpoint / data-check / conditional-format / derivative on view V
cp = step(
    "view.checkpoint.create",
    [
        "view",
        "checkpoint",
        "create",
        V,
        D,
        "--input",
        J({"body": {"checkpoint_name": "ev-cp", "checkpoint_type": "alert"}}),
    ],
)
cpid = str((cp or {}).get("id") or (cp or {}).get("checkpoint_id") or 1)
step("view.checkpoint.get", ["view", "checkpoint", "get", V, cpid, D])
step(
    "view.checkpoint.update",
    [
        "view",
        "checkpoint",
        "update",
        V,
        cpid,
        D,
        "--input",
        J({"body": {"patches": [{"op": "command", "path": "approve", "value": None}]}}),
    ],
)
step("view.checkpoint.delete", ["view", "checkpoint", "delete", V, cpid, D, "--yes"])

dc = step(
    "view.data-check.create",
    [
        "view",
        "data-check",
        "create",
        V,
        D,
        "--input",
        J(
            {
                "body": {
                    "name": "ev-dc",
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
dcid = str((dc or {}).get("id") or (dc or {}).get("data_check_id") or 1)
step("view.data-check.get", ["view", "data-check", "get", V, dcid, D])
step(
    "view.data-check.update",
    [
        "view",
        "data-check",
        "update",
        V,
        dcid,
        D,
        "--input",
        J({"body": {"patches": [{"op": "command", "path": "disable", "value": None}]}}),
    ],
)
step("view.data-check.delete", ["view", "data-check", "delete", V, dcid, D, "--yes"])

cf = step(
    "view.conditional-format.create",
    [
        "view",
        "conditional-format",
        "create",
        V,
        D,
        "--input",
        J({"columns": ["amount"], "operator": "<", "value": 5, "color": "red"}),
    ],
)
step(
    "view.conditional-format.update",
    [
        "view",
        "conditional-format",
        "update",
        V,
        D,
        "--input",
        J({"rule": {"patch": []}}),
    ],
)
step(
    "view.conditional-format.delete-all",
    ["view", "conditional-format", "delete-all", V, D, "--yes"],
)

mt = {
    "METRIC": {
        "AS": "ev_metric",
        "EXPRESSION": [
            {"TYPE": "FUNCTION", "VALUE": {"ARGUMENT": "column_4", "FUNCTION": "SUM"}}
        ],
    }
}
dv = step(
    "view.derivative.create",
    ["view", "derivative", "create", V, D, "--input", J({"body": {"param": mt}})],
)
dvid = str((dv or {}).get("id") or (dv or {}).get("derivative_id") or 1)
step(
    "view.derivative.data",
    ["view", "derivative", "data", V, dvid, D, "--input", J({"body": {"limit": None}})],
)
mt2 = {
    "METRIC": {
        "AS": "ev_metric2",
        "EXPRESSION": [
            {"TYPE": "FUNCTION", "VALUE": {"ARGUMENT": "column_4", "FUNCTION": "AVG"}}
        ],
    }
}
step(
    "view.derivative.update",
    [
        "view",
        "derivative",
        "update",
        V,
        dvid,
        D,
        "--input",
        J({"body": {"patches": [{"op": "replace", "path": "param", "value": mt2}]}}),
    ],
)
step("view.derivative.delete", ["view", "derivative", "delete", V, dvid, D, "--yes"])

step("view.active-user.mark", ["view", "active-user", "mark", V, D])

# --- pipeline / tasks (view V gets two tasks)
add = step(
    "view.task.add",
    [
        "view",
        "task",
        "add",
        V,
        "--input",
        J(
            {
                "dataset_id": ds,
                "task_spec": {
                    "DATAVIEW_ID": vid,
                    "SEQUENCE_NUMBER": 1,
                    "COPY": [
                        {
                            "SOURCE": "column_4",
                            "AS": {
                                "COLUMN": "ev_copy",
                                "TYPE": "NUMERIC",
                                "INTERNAL_NAME": "column_90",
                            },
                        }
                    ],
                    "VERSION": 2,
                },
            }
        ),
    ],
)
code, env = run(["view", "task", "list", V, "--input", J({"dataset_id": ds})], PROF, P)
tasks = (env.get("data") or {}).get("tasks") or []
tid = str(tasks[0]["id"]) if tasks else None
step(
    "view.task.preview",
    [
        "view",
        "task",
        "preview",
        V,
        "--input",
        J(
            {
                "dataset_id": ds,
                "task_spec": {
                    "DATAVIEW_ID": vid,
                    "SEQUENCE_NUMBER": 2,
                    "COPY": [
                        {
                            "SOURCE": "column_3",
                            "AS": {
                                "COLUMN": "ev_prev",
                                "TYPE": "TEXT",
                                "INTERNAL_NAME": "column_91",
                            },
                        }
                    ],
                    "VERSION": 2,
                },
            }
        ),
    ],
)
if tid:
    step(
        "view.task.update",
        [
            "view",
            "task",
            "update",
            V,
            tid,
            "--input",
            J(
                {
                    "dataset_id": ds,
                    "task_spec": {
                        "DATAVIEW_ID": vid,
                        "SEQUENCE_NUMBER": 1,
                        "COPY": [
                            {
                                "SOURCE": "column_4",
                                "AS": {
                                    "COLUMN": "ev_copy2",
                                    "TYPE": "NUMERIC",
                                    "INTERNAL_NAME": "column_90",
                                },
                            }
                        ],
                        "VERSION": 2,
                    },
                }
            ),
        ],
    )
step(
    "view.pipeline.edit",
    [
        "view",
        "pipeline",
        "edit",
        V,
        "--input",
        J(
            {
                "dataset_id": ds,
                "patches": [{"op": "replace", "path": "auto_run", "value": True}],
            }
        ),
    ],
)
step(
    "view.pipeline.rerun",
    ["view", "pipeline", "rerun", V, "--input", J({"dataset_id": ds})],
)
step(
    "view.draft.command",
    [
        "view",
        "draft",
        "command",
        V,
        "--input",
        J({"dataset_id": ds, "command": "enter"}),
    ],
)
step(
    "view.draft.command",
    [
        "view",
        "draft",
        "command",
        V,
        "--input",
        J({"dataset_id": ds, "command": "discard"}),
    ],
    note="discard",
)
if tid:
    step(
        "view.task.delete",
        ["view", "task", "delete", V, tid, "--input", J({"dataset_id": ds}), "--yes"],
    )
code, env = run(["view", "version", "list", V, D], PROF, P)
vers = (
    [x for x in (env.get("data") or {}).get("versions", [])]
    if isinstance(env.get("data"), dict)
    else []
)
vv = str(vers[-1]["id"]) if vers else None
if vv:
    step("view.version.apply", ["view", "version", "apply", V, vv, D])
    step(
        "view.version.update",
        [
            "view",
            "version",
            "update",
            V,
            vv,
            D,
            "--input",
            J(
                {
                    "body": {
                        "patches": [
                            {"op": "replace", "path": "name", "value": "ev-version"}
                        ]
                    }
                }
            ),
        ],
    )
    step("view.version.delete", ["view", "version", "delete", V, vv, D, "--yes"])
else:
    rows.append(
        {
            "command_id": "view.version.apply",
            "verdict": "blocked_missing_fixture",
            "note": "view version list returned no versions",
        }
    )

# --- exports (csv only; no external destinations)
ex = step(
    "view.export.create",
    [
        "view",
        "export",
        "create",
        V,
        "--input",
        J(
            {
                "dataset_id": ds,
                "export_spec": {
                    "DATAVIEW_ID": vid,
                    "handler_type": "csv_file",
                    "trigger_type": "none",
                    "target_properties": {
                        "file": "ev_export",
                        "file_type": "csv",
                        "include_hidden": False,
                    },
                },
            }
        ),
        "--yes",
    ],
)
exid = str((ex or {}).get("id") or (ex or {}).get("export_id") or 1)
step(
    "view.export.update",
    [
        "view",
        "export",
        "update",
        V,
        exid,
        "--input",
        J(
            {
                "dataset_id": ds,
                "patches": [
                    {
                        "op": "replace",
                        "path": "target_properties|params",
                        "value": {
                            "file": "ev_export2",
                            "file_type": "csv",
                            "include_hidden": False,
                        },
                    }
                ],
            }
        ),
        "--yes",
    ],
)
step(
    "view.export.delete",
    ["view", "export", "delete", V, exid, "--input", J({"dataset_id": ds}), "--yes"],
)

# --- AI (one call each)
step(
    "view.ai.generate-data",
    [
        "view",
        "ai",
        "generate-data",
        V,
        "--input",
        J({"dataset_id": ds, "prompt": "add 3 more stores", "no_of_rows": 3}),
    ],
)
step(
    "ai.condition.generate",
    [
        "ai",
        "condition",
        "generate",
        D,
        "--input",
        J({"intent": "rows in boston", "dataview_id": vid}),
    ],
)

# --- view lifecycle on a view of ds2
step("view.trash", ["view", "trash", str(vid2), str(ds2)])
step("view.restore", ["view", "restore", str(vid2), str(ds2)])
step(
    "view.update",
    ["view", "update", str(vid2), str(ds2), "--input", J({"name": "ev-renamed"})],
)
c2 = run(["view", "create", str(ds2), "--input", J({"name": "ev-extra"})], PROF, P)[1][
    "data"
]["id"]
c3 = run(["view", "create", str(ds2), "--input", J({"name": "ev-extra2"})], PROF, P)[1][
    "data"
]["id"]
step("view.delete", ["view", "delete", str(c2), str(ds2), "--yes"])
step(
    "view.bulk-delete",
    ["view", "bulk-delete", str(ds2), "--input", J({"dataview_ids": [c3]}), "--yes"],
)

# --- dataset lifecycle
step("dataset.trash", ["dataset", "trash", str(ds3)])
step("dataset.restore", ["dataset", "restore", str(ds3)])
step(
    "dataset.file-settings.undo",
    ["dataset", "file-settings", "undo", str(ds3), "--yes"],
)
step(
    "trash.add",
    ["trash", "add", "--input", J({"items": [{"id": ds3, "type": "dataset"}]})],
)
step(
    "trash.restore",
    ["trash", "restore", "--input", J({"items": [{"id": ds3, "type": "dataset"}]})],
)

# --- batch (append a second file to ds3)
up = run(
    ["file", "upload", FIX, "--input", J({"append_to_ds_id": ds3})],
    PROF,
    P,
    timeout=240,
)
print("append upload", up[0])
rows.append(
    {
        "command_id": "file.upload",
        "note": "append_to_ds_id",
        "exit": up[0],
        "verdict": classify(*up)[0],
    }
)
code, env = run(["batch", "list", str(ds3)], PROF, P)
bl = first = None
bd = env.get("data")
ids = []
if isinstance(bd, (dict, list)):
    items = (
        bd
        if isinstance(bd, list)
        else next((v for v in bd.values() if isinstance(v, list)), [])
    )
    ids = [x.get("id") for x in items if isinstance(x, dict)]
if ids:
    step(
        "batch.update",
        [
            "batch",
            "update",
            str(ds3),
            "--input",
            J({"patch": [{"op": "replace", "path": "name", "value": "ev-batch"}]}),
        ],
    )
    step("batch.delete", ["batch", "delete", str(ds3), str(ids[-1]), "--yes"])
    if len(ids) > 1:
        step(
            "batch.bulk-delete",
            [
                "batch",
                "bulk-delete",
                str(ds3),
                "--input",
                J({"ids": [ids[0]]}),
                "--yes",
            ],
        )
else:
    for c in ("batch.update", "batch.delete", "batch.bulk-delete"):
        rows.append(
            {
                "command_id": c,
                "verdict": "blocked_missing_fixture",
                "note": "no batch listed on the appended dataset",
            }
        )
step(
    "batch.create",
    [
        "batch",
        "create",
        str(ds3),
        str(ds2),
        "--input",
        J({"mapping": {"column_1": "column_1"}}),
    ],
)

# --- files / folders
code, env = run(["file", "list"], PROF, P)
fl = [
    f
    for f in (env.get("data") or {}).get("files") or []
    if f["id"] not in before and str(f.get("name", "")).endswith("fixture.csv")
]
fid = fl[0]["id"] if fl else None
if fid:
    step(
        "file.update",
        [
            "file",
            "update",
            str(fid),
            "--input",
            J(
                {
                    "patch_request": {
                        "patch": [
                            {"op": "replace", "path": "password", "value": "test"}
                        ]
                    }
                }
            ),
        ],
    )
    step("file.delete", ["file", "delete", str(fid), "--yes"])
    if len(fl) > 1:
        step(
            "file.bulk-delete",
            ["file", "bulk-delete", "--input", J({"file_ids": [fl[1]["id"]]}), "--yes"],
        )
fa = (
    run(["folder", "create", "--input", J({"name": "ev-f1"})], PROF, P)[1].get("data")
    or {}
)
fb = (
    run(["folder", "create", "--input", J({"name": "ev-f2"})], PROF, P)[1].get("data")
    or {}
)
fc = (
    run(["folder", "create", "--input", J({"name": "ev-f3"})], PROF, P)[1].get("data")
    or {}
)
print("folders", fa.get("id"), fb.get("id"), fc.get("id"))
if fa.get("id") and fb.get("id"):
    step(
        "folder.move",
        [
            "folder",
            "move",
            "--input",
            J(
                {
                    "resource_ids": [str(fa.get("resource_id"))],
                    "target_folder_resource_id": str(fb.get("resource_id")),
                }
            ),
        ],
    )
    step("folder.trash", ["folder", "trash", str(fc["id"])])
    step(
        "folder.bulk-delete",
        [
            "folder",
            "bulk-delete",
            "--input",
            J({"folder_ids": [fa["id"], fb["id"]]}),
            "--yes",
        ],
    )

json.dump(
    {"ds": [ds, ds2, ds3], "views": [vid, vid2, vid3]},
    open("/tmp/claude-1000/out/created_write.json", "w"),
)
with open(OUT, "w") as f:
    for r in rows:
        f.write(json.dumps(r, sort_keys=True) + "\n")
