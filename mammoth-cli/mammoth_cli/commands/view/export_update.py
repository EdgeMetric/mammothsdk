"""Merge-style ``view export update``: patches the server accepts, pinned to the pipeline end."""

from __future__ import annotations

from typing import Any

PATCH_OP_COMMAND = "command"
PATCH_OP_REPLACE = "replace"
PATCH_PATH_PARAMS = "params"
#: ``--input`` keys that edit the stored export without writing a patch list.
SHORTHAND_FIELDS = (
    "save_as_mode",
    "target_properties",
    "additional_properties",
    "condition",
    "trigger_type",
    "handler_type",
    "end_of_pipeline",
    "sequence",
    "run_immediately",
)
#: ``target_properties`` key holding the write mode of an export into a dataset.
SAVE_AS_MODE_KEY = "SAVE_AS_DS_MODE"
_STORED_SPEC_FIELDS = (
    "handler_type",
    "trigger_type",
    "target_properties",
    "additional_properties",
    "condition",
)
#: The fields of the server's export spec a caller may set (anything else in a copy of
#: ``view export get``, such as ``id`` or ``status``, is read-only and left out).
_SPEC_FIELDS = (
    *_STORED_SPEC_FIELDS,
    "DATAVIEW_ID",
    "TRIGGER_ID",
    "run_immediately",
    "validate_only",
)


def has_shorthand(document: dict[str, Any] | None) -> bool:
    """Whether ``document`` edits the export through the shorthand fields.

    Args:
        document: The parsed ``--input`` document, or None.

    Returns:
        True when any of :data:`SHORTHAND_FIELDS` is present.
    """
    return document is not None and any(field in document for field in SHORTHAND_FIELDS)


def needs_stored_export(patches: list[Any]) -> bool:
    """Whether any patch replaces the whole export params (and so needs the stored export).

    Args:
        patches: The patch operations.

    Returns:
        True when a ``replace`` of ``params`` is among them.
    """
    return any(_is_params_replace(patch) for patch in patches)


def shorthand_patches(document: dict[str, Any]) -> list[dict[str, Any]]:
    """One ``replace params`` patch carrying the shorthand fields of ``document``.

    Args:
        document: The parsed ``--input`` document.

    Returns:
        A single-patch list whose value holds only the fields the caller set.
    """
    value = {field: document[field] for field in SHORTHAND_FIELDS if field in document}
    return [{"op": PATCH_OP_REPLACE, "path": PATCH_PATH_PARAMS, "value": value}]


def normalize_patches(
    patches: list[Any], stored: dict[str, Any] | None, dataview_id: int
) -> list[Any]:
    """Fill what the server demands and merge ``replace params`` over the stored export.

    A ``command`` patch gets ``value: null`` when it has none. A ``replace`` of ``params``
    keeps every field it leaves out from ``stored``, and keeps the export pinned to the end
    of the pipeline unless the patch itself sets ``end_of_pipeline`` to false.

    Args:
        patches: The patch operations as the caller wrote them.
        stored: The export as ``view export get`` returns it, or None when no patch needs it.
        dataview_id: The view the export belongs to.

    Returns:
        The patches to send; other patches are passed through unchanged.
    """
    result: list[Any] = []
    for patch in patches:
        if isinstance(patch, dict) and patch.get("op") == PATCH_OP_COMMAND:
            result.append({**patch, "value": patch.get("value")})
        elif _is_params_replace(patch) and stored is not None:
            result.append({**patch, "value": merged_spec(stored, patch.get("value"), dataview_id)})
        else:
            result.append(patch)
    return result


def merged_spec(stored: dict[str, Any], changes: Any, dataview_id: int) -> dict[str, Any]:
    """The full export spec: ``changes`` over the stored export, pin to the pipeline end kept.

    The server treats ``sequence: null`` as "pin to the end of the pipeline" and any number
    as "unpin", whatever ``end_of_pipeline`` says, so a pinned export always gets null.

    Args:
        stored: The export as ``view export get`` returns it.
        changes: The caller's partial spec (a non-dict counts as no changes).
        dataview_id: The view the export belongs to.

    Returns:
        The spec for a ``replace`` of ``params``.
    """
    given = dict(changes) if isinstance(changes, dict) else {}
    spec: dict[str, Any] = {"DATAVIEW_ID": dataview_id, "run_immediately": False}
    for field in _STORED_SPEC_FIELDS:
        if stored.get(field) is not None:
            spec[field] = stored[field]
    for field in _SPEC_FIELDS:
        if field in given:
            spec[field] = given[field]
    if "save_as_mode" in given:
        spec["target_properties"] = {
            **(spec.get("target_properties") or {}),
            SAVE_AS_MODE_KEY: given["save_as_mode"],
        }
    pinned = given.get("end_of_pipeline", stored.get("end_of_pipeline", True)) is not False
    spec["end_of_pipeline"] = pinned
    spec["sequence"] = None if pinned else given.get("sequence", stored.get("sequence"))
    return spec


def _is_params_replace(patch: Any) -> bool:
    """Whether ``patch`` is a ``replace`` of the whole export params."""
    return (
        isinstance(patch, dict)
        and patch.get("op") == PATCH_OP_REPLACE
        and patch.get("path") == PATCH_PATH_PARAMS
    )
