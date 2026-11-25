"""Set a board's theme and light/dark mode on its v3 canvas (mammothsdk#419).

``dashboard get`` shows the board's ``style`` (``style_id`` and ``mode``); ``dashboard
create-blank`` and ``dashboard update`` take the same two input fields to set them. The
canvas is read, the two keys are set and it is saved back with the sequence that was read.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_API_ERROR,
    CODE_INVALID_ARGUMENT,
    EXIT_API,
    EXIT_USAGE,
    CliError,
)
from mammoth_cli.services.dashboard_pages import CANVAS_SAVE
from mammoth_cli.services.dashboard_review import CANVAS_GET

#: The input fields that choose the board's look.
STYLE_FIELDS = ("style_id", "mode")

#: The modes the canvas takes (``ColorMode`` in the backend's canvas contract).
MODES = ("light", "dark")


def pop_style_choice(document: dict[str, Any]) -> dict[str, str]:
    """Take ``style_id`` and ``mode`` out of ``document`` and validate them.

    Args:
        document: The bound input document; the style fields are removed from it so they
            never reach the SDK call.

    Returns:
        The fields that were given, e.g. ``{"style_id": "stone", "mode": "dark"}``; empty
        when neither was.

    Raises:
        CliError: If ``mode`` is not ``light`` or ``dark``, or ``style_id`` is not a
            non-blank string.
    """
    choice: dict[str, str] = {}
    for name in STYLE_FIELDS:
        if name not in document:
            continue
        value = document.pop(name)
        if value is None:
            continue
        if name == "mode" and value not in MODES:
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message=f"mode must be one of {', '.join(MODES)}; got {value!r}.",
                exit_status=EXIT_USAGE,
                hint='Use {"mode": "dark"} or {"mode": "light"}.',
            )
        if name == "style_id" and (not isinstance(value, str) or not value.strip()):
            raise CliError(
                code=CODE_INVALID_ARGUMENT,
                message="style_id must be a non-blank theme id string.",
                exit_status=EXIT_USAGE,
                hint=(
                    "Read the current one with 'mammoth dashboard get ID' (style.style_id); "
                    "custom themes: 'mammoth dashboard style custom list'."
                ),
            )
        choice[name] = value.strip() if name == "style_id" else value
    return choice


def _dump(value: Any) -> Any:
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else value


def save_board_style(service: Any, dashboard_id: int, choice: Mapping[str, str]) -> dict[str, Any]:
    """Set the chosen theme and mode on the board's canvas and save it.

    The canvas is read, changed and saved with the sequence that was read, so a board edited
    in between is refused instead of overwritten. That guard needs ``meta.sequence`` in the canvas
    read; without one the save is sent unguarded. A new ``style_id`` clears the canvas's
    ``style_tokens``: the renderer prefers inlined tokens, so they would keep the old look.

    Args:
        service: The session service.
        dashboard_id: The board to restyle.
        choice: ``style_id`` and/or ``mode`` from :func:`pop_style_choice`.

    Returns:
        ``{"style": {...}, "sequence": ..., "bake_job_id": ...}``; the last two only when the
        save answered them. The caller waits for the bake.

    Raises:
        CliError: If the canvas read carries no canvas.
    """
    doc = _dump(service.call(CANVAS_GET, dashboard_id=dashboard_id))
    canvas = doc.get("canvas") if isinstance(doc, dict) else None
    if not isinstance(canvas, dict):
        raise CliError(
            code=CODE_API_ERROR,
            message=f"Dashboard {dashboard_id} returned no canvas, so its style was not set.",
            exit_status=EXIT_API,
        )
    canvas = {**canvas, **choice}
    if "style_id" in choice:
        canvas.pop("style_tokens", None)
    params: dict[str, Any] = {"canvas": canvas}
    meta = doc.get("meta")
    if isinstance(meta, dict) and isinstance(meta.get("sequence"), int):
        params["base_sequence"] = meta["sequence"]
    saved = _dump(service.call(CANVAS_SAVE, dashboard_id=dashboard_id, body={"params": params}))
    result: dict[str, Any] = {
        "style": {key: canvas[key] for key in STYLE_FIELDS if canvas.get(key)}
    }
    if isinstance(saved, dict):
        for key in ("sequence", "bake_job_id"):
            if key in saved:
                result[key] = saved[key]
    return result
