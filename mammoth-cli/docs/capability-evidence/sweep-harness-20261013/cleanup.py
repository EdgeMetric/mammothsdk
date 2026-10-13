import json

from sweeplib import classify, run

P, PF = 25654, "koyal"
ids = [88928, 88929, 88930, 88931, 88932, 88933, 88934, 88936]
c, e = run(
    ["dataset", "bulk-delete", "--input", json.dumps({"dataset_ids": ids}), "--yes"],
    PF,
    P,
    timeout=240,
)
v, info = classify(c, e)
print(c, v, json.dumps(e)[:400])
row = {
    "command_id": "dataset.bulk-delete",
    "argv": "dataset bulk-delete --input {dataset_ids:[8 own fixture datasets]} --yes",
    "exit": c,
    "verdict": v,
    **info,
    "note": "cleanup of the sweep's own fixtures",
}
open("/tmp/claude-1000/out/cleanup.jsonl", "w").write(json.dumps(row) + "\n")
c, e = run(["dataset", "list"], PF, P)
print([(x["id"], x["name"]) for x in e["data"]["datasets"]])
c, e = run(["file", "list"], PF, P)
print([(x["id"], x.get("name")) for x in e["data"].get("files") or []])
