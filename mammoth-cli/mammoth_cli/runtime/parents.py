"""A local memory of which dataset owns which view.

Every view command that changes, exports or deletes data needs the view's
parent dataset, because the backend addresses views under their dataset and
the only alternative is a project-wide browse-and-probe walk that the CLI
refuses to run before a mutation. Agents therefore had to carry
``dataset_id`` from a read into every later call.

The pair never changes (a view lives in exactly one dataset for its whole
life), so it is remembered the first time any command observes it — ``view
list``, ``view get``, ``view create``, a read that resolved the parent — and
consulted whenever a later command omits the parent. An explicit
``DATASET_ID`` or ``dataset_id`` field always wins; the cache only fills a
gap. Entries are keyed by profile and workspace so two tenants never mix.

The file lives next to the run log in the platform state directory
(``MAMMOTH_PARENT_CACHE`` overrides the path). It holds ids only.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import platformdirs

CACHE_ENV = "MAMMOTH_PARENT_CACHE"
#: Oldest entries are dropped past this many; a workspace rarely has more.
MAX_ENTRIES = 5000


def cache_path() -> Path:
    override = os.environ.get(CACHE_ENV)
    if override:
        return Path(override).expanduser()
    return Path(platformdirs.user_state_dir("mammoth-cli", "Mammoth")) / "view-parents.json"


def _key(profile: str | None, workspace_id: int | None, view_id: int) -> str:
    return f"{profile or 'default'}|{workspace_id or 0}|{int(view_id)}"


def _read() -> dict[str, Any]:
    try:
        document = json.loads(cache_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return document if isinstance(document, dict) else {}


def _write(document: dict[str, Any]) -> None:
    path = cache_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(document, separators=(",", ":")) + "\n", encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        return


def lookup(profile: str | None, workspace_id: int | None, view_id: int) -> int | None:
    """The remembered parent dataset of ``view_id``, or None."""
    entry = _read().get(_key(profile, workspace_id, view_id))
    if not isinstance(entry, dict):
        return None
    dataset_id = entry.get("dataset_id")
    return int(dataset_id) if isinstance(dataset_id, int) and dataset_id > 0 else None


def remember(
    profile: str | None,
    workspace_id: int | None,
    pairs: dict[int, int] | list[tuple[int, int]],
    *,
    project_id: int | None = None,
) -> None:
    """Record ``view_id -> dataset_id`` pairs; a no-op when nothing is new."""
    items = pairs.items() if isinstance(pairs, dict) else pairs
    document = _read()
    changed = False
    for view_id, dataset_id in items:
        if not (isinstance(view_id, int) and isinstance(dataset_id, int) and dataset_id > 0):
            continue
        key = _key(profile, workspace_id, view_id)
        entry = {"dataset_id": dataset_id}
        if project_id is not None:
            entry["project_id"] = int(project_id)
        if document.get(key) != entry:
            document[key] = entry
            changed = True
    if not changed:
        return
    if len(document) > MAX_ENTRIES:
        for stale in list(document)[: len(document) - MAX_ENTRIES]:
            document.pop(stale, None)
    _write(document)


def remember_records(
    profile: str | None,
    workspace_id: int | None,
    records: Any,
    *,
    project_id: int | None = None,
) -> None:
    """Harvest ``{id, dataset_id}`` pairs from a payload (a record or a list of them)."""
    pairs: list[tuple[int, int]] = []
    candidates: list[Any]
    if isinstance(records, dict):
        nested = records.get("dataviews") or records.get("views") or records.get("items")
        candidates = list(nested) if isinstance(nested, list) else [records]
    elif isinstance(records, list):
        candidates = records
    else:
        candidates = []
    for record in candidates:
        if not isinstance(record, dict):
            continue
        view_id = record.get("id", record.get("view_id", record.get("dataview_id")))
        # The backend's dataview record names its parent ``ds_id``; SDK View
        # payloads and older fixtures say ``dataset_id``.
        dataset_id = record.get("ds_id", record.get("dataset_id"))
        if isinstance(view_id, int) and isinstance(dataset_id, int):
            pairs.append((view_id, dataset_id))
    if pairs:
        remember(profile, workspace_id, pairs, project_id=project_id)
