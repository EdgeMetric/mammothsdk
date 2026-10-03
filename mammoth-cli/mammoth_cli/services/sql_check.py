"""Check a SQL step's column names against what it will bind to, before it is added.

``FROM "view:<id>"`` binds to the names the pipeline produced (the ``metadata`` of the
view's latest data), not to a display-only rename (``display_properties.COLUMN_NAMES``),
which ``view get`` shows. A query naming the renamed column is accepted by the CLI and
fails in the backend's DuckDB with a Binder Error, so a dry run says so first.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

from mammoth_cli.errors.envelope import CODE_WOULD_FAIL, EXIT_USAGE, CliError

_STRING = re.compile(r"'(?:[^']|'')*'")
_QUOTED = re.compile(r'"((?:[^"]|"")+)"')
_ALIAS = re.compile(r'\bAS\s+("(?:[^"]|"")+"|\w+)|("(?:[^"]|"")+"|\w+)\s+AS\s*\(', re.IGNORECASE)
_TABLE = re.compile(r'\b(?:FROM|JOIN)\s+("(?:[^"]|"")+")', re.IGNORECASE)
_VIEW_REF = re.compile(r"view:\d+")


def _unquote(name: str) -> str:
    return name[1:-1].replace('""', '"') if name.startswith('"') else name


def _declared(query: str) -> set[str]:
    """Names the query itself introduces (aliases, CTEs) or reads as a table."""
    aliases = {_unquote(a or b) for a, b in _ALIAS.findall(query)}
    tables = {_unquote(t) for t in _TABLE.findall(query)}
    return {name.casefold() for name in aliases | tables}


def _identifiers(query: str, renamed: Mapping[str, str]) -> list[str]:
    """Quoted identifiers, plus any bare word that is a renamed column's new name."""
    found = [m for m in _QUOTED.findall(query) if not _VIEW_REF.fullmatch(m)]
    words = {w.casefold() for w in re.findall(r"\w+", _QUOTED.sub(" ", query))}
    found += [new for new in renamed if new.casefold() in words]
    return list(dict.fromkeys(name.replace('""', '"') for name in found))


def _renames(view: Mapping[str, object]) -> dict[str, str]:
    """``{new name: pipeline name}`` for each display-only rename of the view."""
    display = view.get("display_properties")
    names = display.get("COLUMN_NAMES") if isinstance(display, dict) else None
    metadata = view.get("metadata")
    if not isinstance(names, dict) or not isinstance(metadata, list):
        return {}
    by_internal = {c.get("internal_name"): c.get("display_name") for c in metadata}
    return {new: by_internal[i] for i, new in names.items() if by_internal.get(i)}


def check_sql_binds(query: str, view: Mapping[str, object]) -> None:
    """Raise ``would_fail`` when ``query`` names a column the step cannot bind.

    Args:
        query: The step's SQL.
        view: The raw ``dataview get`` record (its ``metadata`` is the bindable schema).

    Raises:
        CliError: ``would_fail``, with the unknown name and the candidate columns.
    """
    metadata = view.get("metadata")
    rows = metadata if isinstance(metadata, list) else []
    columns = [
        str(c["display_name"]) for c in rows if isinstance(c, dict) and c.get("display_name")
    ]
    if not columns:
        return
    renamed = _renames(view)
    text = _STRING.sub("''", query)
    known = {c.casefold() for c in columns} | _declared(text)
    for name in _identifiers(text, renamed):
        if name.casefold() not in known:
            raise _unbound(name, columns, renamed.get(name))


def _unbound(name: str, columns: list[str], was: str | None) -> CliError:
    hint = f'Use "{was}": "{name}" is only a display name for it.' if was else None
    return CliError(
        code=CODE_WOULD_FAIL,
        message=f'Referenced column "{name}" not found. Candidate bindings: '
        + ", ".join(f'"{c}"' for c in columns),
        exit_status=EXIT_USAGE,
        hint=hint or "Use one of the candidate columns; nothing was added.",
        details={"unknown_column": name, "candidate_columns": columns},
    )
