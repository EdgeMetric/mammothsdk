import json

from sweeplib import run

P, PF = 25654, "koyal"
c, e = run(["dataset", "list"], PF, P)
print([(x["id"], x["name"]) for x in e["data"]["datasets"]])
c, e = run(
    [
        "dataset",
        "bulk-delete",
        "--input",
        json.dumps({"dataset_ids": [88930]}),
        "--yes",
    ],
    PF,
    P,
    timeout=240,
)
print(c, json.dumps(e)[:300])
c, e = run(
    [
        "file",
        "bulk-delete",
        "--input",
        json.dumps({"file_ids": [2222, 2223, 2224, 2225, 2228]}),
        "--yes",
    ],
    PF,
    P,
    timeout=240,
)
print(c, json.dumps(e)[:300])
c, e = run(["dataset", "list"], PF, P)
print([(x["id"], x["name"]) for x in e["data"]["datasets"]])
c, e = run(["file", "list"], PF, P)
print([(x["id"], x.get("name")) for x in e["data"].get("files") or []])
