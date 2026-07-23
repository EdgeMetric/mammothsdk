#!/usr/bin/env python3
"""Test all API methods returning Pydantic models against live API."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, ".")

from mammoth import MammothClient

client = MammothClient(
    api_key=os.environ["MAMMOTH_API_KEY"],
    api_secret=os.environ["MAMMOTH_API_SECRET"],
    workspace_id=int(os.environ.get("MAMMOTH_WORKSPACE_ID", "304")),
    base_url=os.environ.get("MAMMOTH_BASE_URL", "https://app.mammoth.io/api/v2"),
    timeout=15,
    job_timeout=30,
)
client.set_project_id(int(os.environ.get("MAMMOTH_PROJECT_ID", "1134")))

passed = 0
failed = 0
errors: list[str] = []


def test(name: str, fn):
    global passed, failed
    try:
        result = fn()
        print(f"  PASS  {name} -> {type(result).__name__}", flush=True)
        passed += 1
        return result
    except Exception as e:
        msg = str(e)[:120]
        print(f"  FAIL  {name} -> {type(e).__name__}: {msg}", flush=True)
        errors.append(f"{name}: {msg}")
        failed += 1
        return None


# ── Files ──
print("=== FilesAPI ===", flush=True)
files_list = test("files.list()", lambda: client.files.list())
if files_list and files_list.files:
    fid = files_list.files[0].id
    test(f"files.get({fid})", lambda: client.files.get(fid))

# ── Folders ──
print("\n=== FoldersAPI ===", flush=True)
folders_list = test("folders.list()", lambda: client.folders.list())
if folders_list:
    print(f"         count={len(folders_list.folders)}", flush=True)
root = test("folders.get_project_root()", lambda: client.folders.get_project_root())
if root:
    print(f"         .name={root.name}  .resource_id={root.resource_id}", flush=True)
folder = test("folders.create()", lambda: client.folders.create(name="__test_validate__"))
if folder and folder.id:
    print(
        f"         .id={folder.id}  .resource_id={folder.resource_id} ({type(folder.resource_id).__name__})",
        flush=True,
    )
    test("folders.delete()", lambda: client.folders.delete(folder_ids=[folder.id]))

# ── Projects ──
print("\n=== ProjectsAPI ===", flush=True)
proj = test("projects.create()", lambda: client.projects.create(name="__test_validate__"))
if proj and proj.get("id"):
    proj_id = proj["id"]
    print(f"         .id={proj_id}  .name={proj['name']}", flush=True)
    test("projects.delete()", lambda: client.projects.delete(proj_id))

# ── Exports ──
print("\n=== ExportsAPI ===", flush=True)
datasets_resp = client.datasets.list()
ds_id = datasets_resp["datasets"][0]["id"] if datasets_resp.get("datasets") else None
dvs = client.dataviews.list(dataset_id=ds_id) if ds_id else {}
if dvs.get("dataviews"):
    vid = dvs["dataviews"][0]["id"]
    test(f"exports.list(dv={vid})", lambda: client.exports.list(dataview_id=vid))

# ── Summary ──
print(f"\n{'='*50}", flush=True)
print(f"Results: {passed} passed, {failed} failed", flush=True)
if errors:
    print("\nFailed tests:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("All Pydantic model methods validated!")
