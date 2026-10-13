"""Re-run read commands the generic fixture binder could not feed (needs a name, parent dataset id, session id)."""

import json
import sys

from sweeplib import classify, run, shape

profile, project, dataset, view, out = (
    sys.argv[1],
    int(sys.argv[2]),
    int(sys.argv[3]),
    int(sys.argv[4]),
    sys.argv[5],
)
rows = []


def step(cid, argv, note=None):
    code, env = run(argv, profile, project)
    v, info = classify(code, env)
    row = {"command_id": cid, "argv": argv, "exit": code, "verdict": v, **info}
    if note:
        row["note"] = note
    if v in ("ok", "ok_empty"):
        row["data_shape"] = shape(env.get("data"))
    rows.append(row)
    print(cid, v, flush=True)
    return env


step("dataset.find", ["dataset", "find", "e"])
step(
    "view.pipeline.items-all",
    [
        "view",
        "pipeline",
        "items-all",
        str(view),
        "--input",
        json.dumps({"dataset_id": dataset}),
    ],
)
c, env = run(
    ["view", "get", str(view), "--input", json.dumps({"dataset_id": dataset})],
    profile,
    project,
)
cols = (
    [x.get("name") for x in (env.get("data") or {}).get("columns") or []]
    if isinstance(env.get("data"), dict)
    else []
)
col = next((n for n in cols if n), None)
if col:
    step(
        "view.data.aggregate",
        [
            "view",
            "data",
            "aggregate",
            str(view),
            "--input",
            json.dumps(
                {
                    "dataset_id": dataset,
                    "aggregations": [
                        {"column": col, "function": "COUNT", "as_name": "n"}
                    ],
                }
            ),
        ],
    )
else:
    rows.append(
        {
            "command_id": "view.data.aggregate",
            "verdict": "blocked_missing_fixture",
            "note": "no column read back from view get",
        }
    )
env = step("agent.session.list", ["agent", "session", "list"])
sess = None
d = env.get("data")
if isinstance(d, dict):
    for v in d.values():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            sess = v[0].get("id") or v[0].get("session_id")
            break
if sess:
    for cid, argv in (
        ("agent.action.list", ["agent", "action", "list"]),
        ("agent.run.list", ["agent", "run", "list"]),
        ("agent.run.status", ["agent", "run", "status"]),
    ):
        step(cid, argv + ["--session", str(sess)])
else:
    for cid in ("agent.action.list", "agent.run.list", "agent.run.status"):
        rows.append(
            {
                "command_id": cid,
                "verdict": "blocked_missing_fixture",
                "note": "no agent session in the workspace",
            }
        )
with open(out, "w") as f:
    for r in rows:
        f.write(json.dumps(r, sort_keys=True) + "\n")
