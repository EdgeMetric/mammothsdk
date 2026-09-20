"""``--dry-run``: resolve a command completely, then stop before its request.

A dry run does everything a real run does up to the network call that the
command exists for — input admission, parent resolution, display-name checks,
condition compilation, argument coercion — and then raises :class:`DryRunStop`
instead of invoking the SDK method. The executor turns that into a success
envelope describing the call that would have been made.

The gate is a small callable installed on the production service by
:func:`mammoth_cli.runtime.session.open_service`. It classifies each SDK call
the handler makes:

- the command's own manifest ``sdk_symbol`` (or, for View-backed commands,
  the View method of that symbol) → stop and report;
- a symbol some ``read`` command is backed by → let it through, so the
  resolution the report depends on really happened;
- anything else → stop and report it as an undeclared write, so a dry run
  can never mutate through a side path.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from enum import Enum
from functools import lru_cache
from typing import Any

from mammoth_cli.manifest.loader import command_by_id, load_commands

Gate = Callable[..., None]

NOTE_OWN = "No request was sent for this operation; the reads needed to resolve it did run."
NOTE_UNDECLARED = (
    "Stopped before an SDK call the command's manifest does not declare; "
    "nothing was sent for it."
)


class DryRunStop(Exception):
    """Raised by the gate at the point a real run would send the request."""

    def __init__(self, record: dict[str, Any]) -> None:
        super().__init__("dry run")
        self.record = record


@lru_cache(maxsize=1)
def _read_symbols() -> frozenset[str]:
    return frozenset(
        str(record["sdk_symbol"])
        for record in load_commands()
        if record.get("mutation_class") == "read" and record.get("sdk_symbol")
    )


def _read_view_methods() -> frozenset[str]:
    return frozenset(
        symbol.rsplit(".", 1)[1]
        for symbol in _read_symbols()
        if symbol.startswith("mammoth.view.") or symbol.startswith("mammoth._mixins.")
    )


def jsonable(value: Any) -> Any:
    """Render resolved SDK arguments for the report without leaking objects."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [jsonable(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        try:
            return jsonable(to_dict())
        except Exception:  # pragma: no cover - defensive; fall through to repr
            return repr(value)
    view_id = getattr(value, "id", None)
    if type(value).__name__ == "View" and isinstance(view_id, int):
        return {"view_id": view_id, "dataset_id": getattr(value, "dataset_id", None)}
    return repr(value)


def make_gate(command_id: str) -> Gate:
    """Return the gate for ``command_id`` (see the module docstring)."""
    record = command_by_id(command_id) or {}
    own_symbol = str(record.get("sdk_symbol") or "")
    own_method = own_symbol.rsplit(".", 1)[-1] if own_symbol else ""
    mutation_class = record.get("mutation_class")
    # A CLI-composed command (project ensure, ...) is backed by a CLI function
    # and reaches the SDK through whichever writes it needs; those are its own.
    composed = own_symbol.startswith("mammoth_cli.")
    reads = _read_symbols()
    view_reads = _read_view_methods()

    def stop(symbol: str, arguments: dict[str, Any], *, own: bool, **scope: Any) -> None:
        raise DryRunStop(
            {
                "dry_run": True,
                "command": command_id.replace(".", " "),
                "mutation_class": mutation_class,
                "would_call": {
                    "sdk_symbol": symbol,
                    **{key: value for key, value in scope.items() if value is not None},
                    "arguments": jsonable(arguments),
                },
                "note": NOTE_OWN if own else NOTE_UNDECLARED,
            }
        )

    def gate(
        symbol: str,
        arguments: dict[str, Any],
        *,
        view_id: int | None = None,
        dataset_id: int | None = None,
    ) -> None:
        if view_id is not None:
            # A View-backed call: ``symbol`` is the View method name.
            if symbol == own_method:
                stop(own_symbol, arguments, own=True, view_id=view_id, dataset_id=dataset_id)
            if symbol in view_reads:
                return
            stop(f"View.{symbol}", arguments, own=False, view_id=view_id, dataset_id=dataset_id)
        if symbol == own_symbol:
            stop(symbol, arguments, own=True)
        if symbol in reads:
            return
        stop(symbol, arguments, own=composed)

    return gate
