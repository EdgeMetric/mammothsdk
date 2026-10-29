"""Merge-style ``view export update``: patches the server accepts, pinned to the pipeline end."""

from __future__ import annotations

from typing import Any

from mammoth_cli.errors.envelope import CODE_INVALID_ARGUMENT, EXIT_USAGE, CliError

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
    "schedule",
    "send_window",
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
#: The server keeps the schedule and the send window inside ``additional_properties``
#: but takes them back only from these top-level spec fields: it strips the stored keys and
#: deregisters the export's ScheduleJob when a save carries neither field.
SCHEDULE_FIELDS = ("schedule", "send_window")
#: Written by the runs themselves (the held send of a send window); never sent back.
_SERVER_OWNED_KEY = "send_window_pending_since"
#: The fields of the server's export spec a caller may set (anything else in a copy of
#: ``view export get``, such as ``id`` or ``status``, is read-only and left out).
_SPEC_FIELDS = (
    *_STORED_SPEC_FIELDS,
    *SCHEDULE_FIELDS,
    "release_moved_schedule",
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
    _carry_schedule(spec, stored, given)
    if "save_as_mode" in given:
        spec["target_properties"] = {
            **(spec.get("target_properties") or {}),
            SAVE_AS_MODE_KEY: given["save_as_mode"],
        }
    pinned = given.get("end_of_pipeline", stored.get("end_of_pipeline", True)) is not False
    if pinned and given.get("sequence") is not None and "end_of_pipeline" not in given:
        raise CliError(
            code=CODE_INVALID_ARGUMENT,
            message=(
                "A sequence cannot be set on an export pinned to the end of the pipeline: "
                "it would be ignored."
            ),
            exit_status=EXIT_USAGE,
            hint='To pin the export at that task, send `"end_of_pipeline": false` with it.',
        )
    spec["end_of_pipeline"] = pinned
    spec["sequence"] = None if pinned else given.get("sequence", stored.get("sequence"))
    return spec


def _carry_schedule(spec: dict[str, Any], stored: dict[str, Any], given: dict[str, Any]) -> None:
    """Put the schedule and send window into ``spec`` as top-level fields.

    The caller's own ``schedule`` / ``send_window`` win; otherwise the ones the export
    stores in ``additional_properties`` are sent back, so an edit does not drop them.

    Args:
        spec: The spec being built; changed in place.
        stored: The export as ``view export get`` returns it.
        given: The caller's partial spec.
    """
    properties = dict(spec.get("additional_properties") or {})
    properties.pop(_SERVER_OWNED_KEY, None)
    stored_properties = stored.get("additional_properties") or {}
    for field in SCHEDULE_FIELDS:
        # Kept from the caller's own properties, else from the stored ones: a caller who sets
        # additional_properties without the schedule does not mean to remove it (a null
        # ``schedule`` / ``send_window`` field does).
        kept = properties.pop(field, None) or stored_properties.get(field)
        if field not in given and kept is not None:
            spec[field] = kept
    if "additional_properties" in spec:
        spec["additional_properties"] = properties


def _is_params_replace(patch: Any) -> bool:
    """Whether ``patch`` is a ``replace`` of the whole export params."""
    return (
        isinstance(patch, dict)
        and patch.get("op") == PATCH_OP_REPLACE
        and patch.get("path") == PATCH_PATH_PARAMS
    )
