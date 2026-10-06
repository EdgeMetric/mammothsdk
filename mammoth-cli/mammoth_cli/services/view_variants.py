"""Plan and report ``view variants create``: one view per value of one column.

The handler composes two existing SDK calls per value (create a view cloned
from the source view, then filter it to the value). This module owns the parts
that need no server: the per-value plan and the result, including the loud
partial-failure error that names every view already created.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mammoth_cli.errors.envelope import (
    CODE_INVALID_ARGUMENTS,
    EXIT_API,
    EXIT_USAGE,
    CliError,
)

DEFAULT_NAME_TEMPLATE = "{view} - {value}"
CODE_VARIANTS_PARTIAL = "variants_partial_failure"
MAX_VARIANTS = 50

type VariantValue = str | int | float


@dataclass(frozen=True)
class VariantPlan:
    """One variant to create: its view name and the filter that defines it."""

    value: VariantValue
    name: str
    condition: dict[str, Any]


def plan_variants(
    source_name: str, column: str, values: list[VariantValue], name_template: str
) -> list[VariantPlan]:
    """Return one plan per value, refusing input that could not make distinct views."""
    if not values:
        raise _invalid("values must name at least one value.")
    if len(values) > MAX_VARIANTS:
        raise _invalid(f"values holds {len(values)} entries; the limit is {MAX_VARIANTS} per call.")
    if len({str(value) for value in values}) != len(values):
        raise _invalid("values must not repeat a value; each value makes one view.")
    plans = [
        VariantPlan(
            value=value,
            name=_render_name(name_template, source_name, value),
            condition={"column": column, "operator": "EQ", "value": value},
        )
        for value in values
    ]
    if len({plan.name for plan in plans}) != len(plans):
        raise _invalid(
            "name_template gives two variants the same name.",
            hint="Include {value} in name_template.",
        )
    return plans


def _render_name(template: str, source_name: str, value: VariantValue) -> str:
    try:
        return template.format(view=source_name, value=value)
    except (KeyError, IndexError, ValueError) as exc:
        raise _invalid(
            f"name_template {template!r} is not valid.",
            hint="Use only {view} and {value}, for example '{view} - {value}'.",
        ) from exc


def _invalid(message: str, hint: str | None = None) -> CliError:
    return CliError(code=CODE_INVALID_ARGUMENTS, message=message, exit_status=EXIT_USAGE, hint=hint)


def created_entry(plan: VariantPlan, view: dict[str, Any]) -> dict[str, Any]:
    """The result row for a variant that was created and filtered."""
    return {"value": plan.value, "view_id": view.get("id"), "name": plan.name}


def variants_result(
    dataset_id: int, from_view: int, column: str, created: list[dict[str, Any]]
) -> dict[str, Any]:
    """The result of a fully created set."""
    return {
        "dataset_id": dataset_id,
        "from_view": from_view,
        "column": column,
        "view_ids": [entry["view_id"] for entry in created],
        "variants": created,
    }


def partial_failure(
    failed: VariantPlan,
    cause: CliError,
    created: list[dict[str, Any]],
    not_attempted: list[VariantPlan],
    orphan_view_id: int | None,
    dataset_id: int,
) -> CliError:
    """The error that stops the run: which variants exist, which failed, which never ran.

    ``orphan_view_id`` is the view that was created for ``failed`` but never got
    its filter (so it holds the unfiltered source rows); the caller deletes or
    fixes it, so it is named, never dropped.
    """
    made = [entry["view_id"] for entry in created]
    skipped = [plan.value for plan in not_attempted]
    recovery = (
        [f"mammoth view delete {orphan_view_id} {dataset_id}"] if orphan_view_id is not None else []
    )
    return CliError(
        code=CODE_VARIANTS_PARTIAL,
        message=(
            f"Variant {failed.value!r} failed ({cause.message}); {len(created)} view(s) were "
            f"created before it: {made}. Not attempted: {skipped}."
        ),
        exit_status=EXIT_API,
        hint=(
            "Rerun with only the failed and not-attempted values. "
            + (
                f"View {orphan_view_id} was created for {failed.value!r} but is not filtered; "
                "delete it before the rerun."
                if orphan_view_id is not None
                else "No half-made view was left behind."
            )
        ),
        details={
            "created": created,
            "failed": {"value": failed.value, "code": cause.code, "message": cause.message},
            "not_attempted": skipped,
            "unfiltered_view_id": orphan_view_id,
        },
        recovery_commands=recovery,
    )
