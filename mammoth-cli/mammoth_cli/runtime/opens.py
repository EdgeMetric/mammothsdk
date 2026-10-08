"""Tell the caller which objects a write made or changed, and where each one opens.

A write's ``meta.opens`` lists ``{kind, id, url, created}`` for every view, dataset,
dashboard, automation, parameter or folder the write made (``created: true``) or
changed (``created: false``). A host that shows the user a link to the result (a chat
receipt) reads it from here instead of working the objects out of each command's own
result shape.

The objects come from the command's manifest ``readback``: an id the readback takes
from the call itself (a positional or an ``--input`` field) is an object that already
existed; an id it takes from the result is one the write made.
"""

from __future__ import annotations

from typing import Any

from mammoth_cli.context.resolver import resolve_auth
from mammoth_cli.manifest.loader import command_by_id
from mammoth_cli.runtime.invocation import Invocation
from mammoth_cli.runtime.state import _resolve_source
from mammoth_cli.services.board_values import dashboard_link
from mammoth_cli.services.positionals import resolve_positionals

#: Kinds of object with a page to open, and the web path (under the project) of each.
_PROJECT_PATHS: dict[str, str] = {
    "view": "views/{id}",
    "dataset": "datasets/{id}",
    "automation": "data/automation",
    "parameter": "data/parameters",
    "folder": "data/folders/{id}",
}
_DASHBOARD = "dashboard"
_OPENABLE = frozenset({*_PROJECT_PATHS, _DASHBOARD})
#: Manifest id names for the same object: a view is ``dataview_id`` in some commands.
_KIND_ALIASES = {"dataview": "view"}
#: Last word of a command that leaves nothing to open.
_GONE_VERBS = frozenset({"trash", "delete"})
#: Kinds a write names in its own result by ``<kind>_id`` without a readback id.
_RESULT_KINDS = ("view", "dashboard")
#: A view export makes a whole new dataset and says so as ``dataset_id`` in its result.
_MAKES_DATASET = frozenset({"view.export.dataset"})
_SOURCE_FROM_CALL = ("positional.", "input.")
_API_SUFFIX = "/api/v2"


def with_opens(invocation: Invocation, data: Any, meta: dict[str, Any]) -> dict[str, Any]:
    """*meta* with ``opens`` added for a write that made or changed an object."""
    record = command_by_id(invocation.command_id) or {}
    if record.get("mutation_class") == "read" or not record.get("sdk_symbol"):
        return meta
    result = data if isinstance(data, dict) else {}
    if invocation.command_id.rsplit(".", 1)[-1] in _GONE_VERBS or _changed_nothing(result):
        return meta
    targets = _targets(invocation, record, result)
    if not targets:
        return meta
    auth = resolve_auth(invocation)
    project_id = meta.get("project_id") or invocation.project
    origin = auth.base_url.rstrip("/").removesuffix(_API_SUFFIX)
    opens = [
        {
            "kind": kind,
            "id": object_id,
            "url": _url(origin, auth.workspace_id, project_id, kind, object_id),
            "created": created,
        }
        for kind, object_id, created in targets
    ]
    return {**meta, "opens": opens}


def _changed_nothing(result: dict[str, Any]) -> bool:
    """Whether the result itself says the command wrote nothing."""
    return (
        result.get("changed") is False
        or result.get("applied") is False
        or result.get("status") == "no_change"
    )


def _targets(
    invocation: Invocation, record: dict[str, Any], result: dict[str, Any]
) -> list[tuple[str, int, bool]]:
    """``(kind, id, created)`` of each openable object the write made or changed."""
    ids = (record.get("readback") or {}).get("ids") or {}
    existing: list[str] = []
    made: list[str] = []
    for name, source in ids.items():
        key = _object_key(str(name), _resolve_source(str(source), result, invocation))
        if key is None:
            continue
        from_call = all(part.startswith(_SOURCE_FROM_CALL) for part in str(source).split("|"))
        (existing if from_call else made).append(key)
    if existing and invocation.command_id not in _MAKES_DATASET:
        made = []
    else:
        made += _result_made(invocation, record, result)
    named = _named_by_call(invocation)
    made = [key for key in made if key not in named]
    keys = dict.fromkeys([*existing, *made])
    targets = [(*key.partition(":")[::2], key in made) for key in keys]
    return [
        (kind, int(object_id), created) for kind, object_id, created in targets if kind in _OPENABLE
    ]


def _result_made(
    invocation: Invocation, record: dict[str, Any], result: dict[str, Any]
) -> list[str]:
    """The ``kind:id`` of each object the result names as ``<kind>_id``."""
    kinds = _RESULT_KINDS
    if invocation.command_id in _MAKES_DATASET or _new_kind(record) == "dataset":
        kinds = ("dataset", *kinds)
    keys = (_object_key(f"{kind}_id", result.get(f"{kind}_id")) for kind in kinds)
    return [key for key in keys if key is not None]


def _new_kind(record: dict[str, Any]) -> str | None:
    """The kind a command makes: it does not edit its target and reads back a result id."""
    readback = record.get("readback") or {}
    if record.get("edits_target") is not False or readback.get("kind") == "delivery":
        return None
    for name, source in (readback.get("ids") or {}).items():
        if str(name).endswith("_id") and str(source).startswith("result."):
            kind = str(name).removesuffix("_id")
            return _KIND_ALIASES.get(kind, kind)
    return None


def _named_by_call(invocation: Invocation) -> set[str]:
    """The ``kind:id`` of each object the call itself names, which it did not make."""
    names = [spec.name for spec in resolve_positionals(invocation.command_id)]
    keys = {
        _object_key(name, value) for name, value in zip(names, invocation.extra_args, strict=False)
    }
    keys |= {_object_key(name, value) for name, value in (invocation.bound_input() or {}).items()}
    return {key for key in keys if key is not None}


def _object_key(name: str, object_id: object) -> str | None:
    """``view:12`` for an id name like ``dataview_id`` and its value."""
    if not name.endswith("_id") or not str(object_id).isdigit():
        return None
    kind = name.removesuffix("_id")
    return f"{_KIND_ALIASES.get(kind, kind)}:{object_id}"


def _url(origin: str, workspace_id: int, project_id: int | None, kind: str, object_id: int) -> str:
    """The web app address of the object (the web app routes by hash)."""
    if kind == _DASHBOARD:
        return dashboard_link(f"{origin}{_API_SUFFIX}", workspace_id, object_id)
    path = _PROJECT_PATHS[kind].format(id=object_id)
    return f"{origin}/#/workspaces/{workspace_id}/projects/{project_id}/{path}"
