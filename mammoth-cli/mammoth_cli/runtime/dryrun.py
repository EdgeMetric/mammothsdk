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

from mammoth_cli.errors.envelope import CODE_RESOURCE_NOT_FOUND, EXIT_NOT_FOUND, CliError
from mammoth_cli.manifest.loader import command_by_id, load_commands
from mammoth_cli.services.protocol import MammothService

Gate = Callable[..., None]

NOTE_OWN = "No request was sent for this operation; the reads needed to resolve it did run."
DATASET_GET = "mammoth.api.datasets.DatasetsAPI.get"
DATAVIEW_GET = "mammoth.api.dataviews.DataviewsAPI.get"
#: The manifest ``mutation_class`` that marks a command as irreversible: the
#: only class whose commands the manifest describes as permanent (no undo).
IRREVERSIBLE_CLASS = "destructive"

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
    # The target-name read is a read whichever command asked for it.
    reads = _read_symbols() | {DATAVIEW_GET}
    view_reads = _read_view_methods()

    def stop(symbol: str, arguments: dict[str, Any], *, own: bool, **scope: Any) -> None:
        raise DryRunStop(
            {
                "dry_run": True,
                "command": command_id.replace(".", " "),
                "mutation_class": mutation_class,
                "irreversible": mutation_class == IRREVERSIBLE_CLASS,
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


def _ids(value: Any) -> list[int]:
    """Return ``value`` as a list of ids (an int, a list of ints, or nothing)."""
    if isinstance(value, bool):
        return []
    if isinstance(value, int):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, int) and not isinstance(item, bool)]
    return []


def _unresolved(kind: str, target_id: int, why: str) -> CliError:
    return CliError(
        code=CODE_RESOURCE_NOT_FOUND,
        message=f"Could not resolve the name of {kind} {target_id} for the dry-run report: {why}.",
        exit_status=EXIT_NOT_FOUND,
        hint=f"Check the id with `mammoth {kind} list`; nothing was changed.",
        details={"type": kind, "id": target_id},
    )


def _named(kind: str, target_id: int, record: Any) -> dict[str, Any]:
    name = record.get("name") if isinstance(record, dict) else None
    if not isinstance(name, str) or not name:
        raise _unresolved(kind, target_id, "the read returned no display name")
    return {"type": kind, "id": target_id, "name": name}


def resolve_targets(
    service: MammothService, command_id: str, would_call: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Name every dataset or view the reported call would change.

    The names come from the same reads the read commands use
    (``DatasetsAPI.get``, ``DataviewsAPI.get``). Commands outside the dataset
    and view families report no targets.

    Args:
        service: An open service (its dry-run gate lets these reads through).
        command_id: The dry-run command's manifest id.
        would_call: The ``would_call`` block of the dry-run report.

    Returns:
        ``[{"type", "id", "name"}, ...]`` in argument order.

    Raises:
        CliError: ``resource_not_found`` when a target has no resolvable name,
            or the read itself fails.
    """
    arguments = would_call.get("arguments") or {}
    project_id = arguments.get("project_id")
    scope = {} if project_id is None else {"project_id": project_id}
    family = command_id.split(".", 1)[0]
    if family == "dataset":
        return [
            _named("dataset", item, service.call(DATASET_GET, dataset_id=item, **scope))
            for item in _ids(arguments.get("dataset_ids") or arguments.get("dataset_id"))
        ]
    if family != "view":
        return []
    view_ids = _ids(
        arguments.get("dataview_ids")
        or arguments.get("dataview_id")
        or arguments.get("view_id")
        or would_call.get("view_id")
    )
    dataset_id = arguments.get("dataset_id") or would_call.get("dataset_id")
    if view_ids and not isinstance(dataset_id, int):
        raise _unresolved("view", view_ids[0], "its parent dataset id is unknown")
    return [
        _named(
            "view",
            item,
            service.call(DATAVIEW_GET, dataset_id=dataset_id, dataview_id=item, **scope),
        )
        for item in view_ids
    ]
