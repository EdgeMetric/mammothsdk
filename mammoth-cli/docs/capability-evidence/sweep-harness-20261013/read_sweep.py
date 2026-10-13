"""Read-only sweep: every `read` command in the catalog, once, on one profile.

usage: read_sweep.py PROFILE PROJECT_ID DATASET_ID OUT.jsonl
Only commands whose mutation_class is `read` are run. Local families that touch
credentials/config are not run.
"""

import json
import sys

from sweeplib import SKIP_FAMILIES, classify, first_id, run, shape

profile, project, dataset, out = (
    sys.argv[1],
    int(sys.argv[2]),
    int(sys.argv[3]),
    sys.argv[4],
)
cat = json.load(open("/tmp/claude-1000/scr/catalog.json"))
LISTS = {
    "file_id": ["file", "list"],
    "folder_id": ["folder", "list"],
    "automation_id": ["automation", "list"],
    "parameter_id": ["parameter", "list"],
    "snippet_id": ["snippet", "list"],
    "webhook_id": ["webhook", "list"],
    "workflow_id": ["workflow", "list"],
    "schedule_id": ["schedule", "list"],
    "data_app_id": ["data-app", "list"],
    "template_id": ["template", "list"],
    "key_id": ["external-key", "list"],
    "batch_id": ["batch", "list"],
    "user_id": ["workspace", "user", "list"],
    "connector_key": ["connector", "list"],
}
fx = {"project_id": project, "dataset_id": dataset}
fx_proj = {}  # command-specific project override (dashboards)
code, env = run(["dataset", "get", str(dataset)], profile, project)
code, env = run(["view", "list"], profile, project)
for v in (env.get("data") or {}).get("dataviews", []):
    if v.get("dataset_id") == dataset:
        fx["view_id"] = fx["dataview_id"] = v["id"]
        break
code, env = run(["dashboard", "list"], profile, None)
dl = env.get("data") or []
if isinstance(dl, list) and dl:
    fx["dashboard_id"] = dl[0]["id"]
    fx["dashboard_project"] = dl[0].get("project_id")
code, env = run(["workspace", "list"], profile, None)
fx["workspace_id"] = first_id(env.get("data"))
tried = set()


def get_fx(name):
    if name in fx:
        return fx[name]
    if name in tried or name not in LISTS:
        return None
    tried.add(name)
    c, e = run(LISTS[name], profile, project)
    keys = ("name_key",) if name == "connector_key" else ("id", "key")
    fx[name] = first_id(e.get("data"), keys) if c == 0 else None
    return fx[name]


COST = {"ai.condition.generate", "ai.expression.generate", "ai.sql.generate", "connector.query.generate"}
rows = []
for c in cat:
    cid = c["command_id"]
    fam = cid.split(".")[0]
    if c["mutation_class"] != "read":
        continue
    if fam in SKIP_FAMILIES:
        rows.append(
            {
                "command_id": cid,
                "verdict": "not_run",
                "note": "local credentials/config family, not run",
            }
        )
        continue
    if cid in COST:
        rows.append({"command_id": cid, "verdict": "not_run", "note": "not re-run (LLM cost)"})
        continue
    s = json.loads(
        __import__("subprocess")
        .run(
            [
                "/tmp/claude-1000/ev-venv/bin/mammoth",
                "schema",
                "get",
                cid,
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
        )
        .stdout
    )["data"]
    argv = c["command_path"].split()
    missing = []
    for p in s["positionals"]:
        if not p.get("required"):
            continue
        v = get_fx(p["name"])
        if v is None:
            missing.append(p["name"])
        else:
            argv.append(str(v))
    extra = {}
    for f in s["accepted_fields"]:
        if f.get("required") and f["name"] not in [p["name"] for p in s["positionals"]]:
            v = get_fx(f["name"])
            if v is None:
                missing.append(f["name"])
            else:
                extra[f["name"]] = v
    if extra:
        argv += ["--input", json.dumps(extra)]
    proj = (
        fx.get("dashboard_project")
        if fam == "dashboard" and fx.get("dashboard_project")
        else project
    )
    row = {"command_id": cid, "argv": argv}
    if missing:
        row.update(
            verdict="blocked_missing_fixture",
            note=f"no fixture for: {', '.join(missing)}",
        )
        rows.append(row)
        continue
    code, env = run(argv, profile, proj)
    v, info = classify(code, env)
    row.update(exit=code, verdict=v, **info)
    if v in ("ok", "ok_empty"):
        row["data_shape"] = shape(env.get("data"))
    rows.append(row)
    print(cid, v, flush=True)
with open(out, "w") as f:
    for r in rows:
        f.write(json.dumps(r, sort_keys=True) + "\n")
