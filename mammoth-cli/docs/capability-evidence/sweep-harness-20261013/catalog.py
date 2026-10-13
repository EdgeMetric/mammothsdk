import json, subprocess, collections

M = "/tmp/claude-1000/ev-venv/bin/mammoth"
fam = json.loads(
    subprocess.run(
        [M, "schema", "list", "--output", "json"], capture_output=True, text=True
    ).stdout
)["data"]["families"]
cat = []
for f in fam:
    o = json.loads(
        subprocess.run(
            [M, "schema", "list", f["family"], "--output", "json"],
            capture_output=True,
            text=True,
        ).stdout
    )["data"]
    cat += o["commands"]
json.dump(cat, open("/tmp/claude-1000/scr/catalog.json", "w"))
print(len(cat), collections.Counter(c["mutation_class"] for c in cat))
base = "/tmp/claude-1000/ev1013/mammoth-cli/docs/capability-evidence/"
rd = {
    json.loads(l)["command_id"]
    for l in open(base + "read-sweep-20260918/results.jsonl")
}
wr = {
    json.loads(l)["command_id"]
    for l in open(base + "write-sweep-20260918/results.jsonl")
}
ids = {c["command_id"]: c["mutation_class"] for c in cat}
print("read-sweep ids missing now", [i for i in rd if i not in ids])
print("write-sweep missing", [i for i in wr if i not in ids])
print(
    collections.Counter(ids.get(i) for i in rd),
    collections.Counter(ids.get(i) for i in wr),
)
print(
    "new read cmds not in old",
    len([i for i, m in ids.items() if m == "read" and i not in rd]),
)
