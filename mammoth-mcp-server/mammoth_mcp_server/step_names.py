"""A pipeline step's columns under the names the user sees.

Mammoth lists a step's params with internal column names (`column_2`), while
every tool takes and reports display names. A step that reads another view (a
join or a lookup) names that view's columns by that view's internal names, so
those are named from the other view's own columns, which Mammoth lists with
the step.
"""

from .consts import ColumnFields, StepFields
from .sdk import JsonValue

# Where a join or a lookup names a column of the OTHER view.
_FOREIGN_PLACES = frozenset(
    {("JOIN", "RIGHT"), ("JOIN", "COLUMN"), ("LOOKUP", "KEY"), ("LOOKUP", "VALUE")}
)
# What a step carries for the web app: column lists by internal name, and a
# join's key analysis. The names in `params` are what a model reads.
_WEB_APP_ONLY = frozenset({StepFields.COLUMNS_READ, StepFields.DISPLAY_INFO})


def _names(columns: JsonValue) -> dict[str, str]:
    """Internal name -> display name, for a list of columns."""
    return {
        str(c[ColumnFields.INTERNAL_NAME]): str(c[ColumnFields.DISPLAY_NAME])
        for c in (columns if isinstance(columns, list) else [])
        if isinstance(c, dict)
        and ColumnFields.INTERNAL_NAME in c
        and ColumnFields.DISPLAY_NAME in c
    }


def _foreign_names(step: dict[str, JsonValue]) -> dict[str, str]:
    """The other view's columns a join or a lookup uses, as Mammoth lists them with the step."""
    info = step.get(StepFields.DISPLAY_INFO)
    analysis = info.get("analysis") if isinstance(info, dict) else None
    used = analysis.get("foreign_columns_used") if isinstance(analysis, dict) else None
    return _names(list(used.values()) if isinstance(used, dict) else [])


def _renamed(
    value: JsonValue, own: dict[str, str], foreign: dict[str, str], place: tuple[str, ...]
) -> JsonValue:
    """`value` with every column name in it shown as the user sees it."""
    if isinstance(value, dict):
        return {
            own.get(key, key): _renamed(item, own, foreign, (*place, key))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_renamed(item, own, foreign, place) for item in value]
    if isinstance(value, str):
        outer = next((key for key in place if key in ("JOIN", "LOOKUP")), None)
        if outer is not None and place and (outer, place[-1]) in _FOREIGN_PLACES:
            return foreign.get(value, value)
        return own.get(value, value)
    return value


def with_display_names(steps: list[JsonValue], view_columns: list[JsonValue]) -> list[JsonValue]:
    """The steps with their params under display names, without the web app's column lists.

    Args:
        steps: The pipeline's steps, as Mammoth lists them.
        view_columns: The view's columns now, which name what the last steps added.
    """
    own = _names(view_columns)
    for step in steps:
        if isinstance(step, dict):
            own = {**_names(step.get(StepFields.COLUMNS_READ)), **own}
    named: list[JsonValue] = []
    for step in steps:
        if not isinstance(step, dict):
            named.append(step)
            continue
        kept = {key: item for key, item in step.items() if key not in _WEB_APP_ONLY}
        if StepFields.PARAMS in step:
            kept[StepFields.PARAMS] = _renamed(
                step[StepFields.PARAMS], own, _foreign_names(step), ()
            )
        named.append(kept)
    return named
