"""``view variants create``: the per-value plan and the loud partial-failure report."""

from __future__ import annotations

import pytest

from mammoth_cli.errors.envelope import EXIT_API, EXIT_USAGE, CliError
from mammoth_cli.services.view_variants import (
    CODE_VARIANTS_PARTIAL,
    DEFAULT_NAME_TEMPLATE,
    MAX_VARIANTS,
    created_entry,
    partial_failure,
    plan_variants,
    variants_result,
)


def test_each_value_becomes_one_named_equality_filter() -> None:
    plans = plan_variants("Sales", "Region", ["East", "West"], DEFAULT_NAME_TEMPLATE)

    assert [plan.name for plan in plans] == ["Sales - East", "Sales - West"]
    assert plans[1].condition == {"column": "Region", "operator": "EQ", "value": "West"}


def test_numeric_values_keep_their_type_in_the_filter() -> None:
    plans = plan_variants("Sales", "Year", [2023, 2024], "{view} {value}")

    assert [plan.condition["value"] for plan in plans] == [2023, 2024]
    assert [plan.name for plan in plans] == ["Sales 2023", "Sales 2024"]


@pytest.mark.parametrize(
    ("values", "template", "needle"),
    [
        ([], DEFAULT_NAME_TEMPLATE, "at least one"),
        (["a", "a"], DEFAULT_NAME_TEMPLATE, "repeat"),
        ([1, "1"], DEFAULT_NAME_TEMPLATE, "repeat"),
        (["a", "b"], "{view}", "same name"),
        (["a"], "{nope}", "not valid"),
        (["a"], "{view", "not valid"),
        (list(range(MAX_VARIANTS + 1)), DEFAULT_NAME_TEMPLATE, "limit"),
    ],
)
def test_input_that_cannot_make_distinct_views_is_refused_as_usage(
    values: list[str | int], template: str, needle: str
) -> None:
    with pytest.raises(CliError) as refused:
        plan_variants("Sales", "Region", list(values), template)

    assert refused.value.exit_status == EXIT_USAGE
    assert needle in refused.value.message


def test_a_full_run_lists_the_view_ids_in_value_order() -> None:
    plans = plan_variants("Sales", "Region", ["East", "West"], DEFAULT_NAME_TEMPLATE)
    created = [created_entry(plan, {"id": 100 + i}) for i, plan in enumerate(plans)]

    result = variants_result(7, 3, "Region", created)

    assert result["view_ids"] == [100, 101]
    assert result["variants"][1] == {"value": "West", "view_id": 101, "name": "Sales - West"}


def test_a_partial_failure_names_what_exists_what_failed_and_what_never_ran() -> None:
    plans = plan_variants("Sales", "Region", ["East", "West", "North"], DEFAULT_NAME_TEMPLATE)
    done = [created_entry(plans[0], {"id": 100})]

    error = partial_failure(
        plans[1], CliError(code="api_error", message="boom"), done, plans[2:], 101, 7
    )

    assert error.code == CODE_VARIANTS_PARTIAL
    assert error.exit_status == EXIT_API
    assert error.details["created"] == done
    assert error.details["failed"] == {"value": "West", "code": "api_error", "message": "boom"}
    assert error.details["not_attempted"] == ["North"]
    assert error.details["unfiltered_view_id"] == 101
    assert error.recovery_commands == ["mammoth view delete 101 7"]
    assert "[100]" in error.message


def test_a_failure_before_the_view_existed_leaves_nothing_to_delete() -> None:
    plans = plan_variants("Sales", "Region", ["East"], DEFAULT_NAME_TEMPLATE)

    error = partial_failure(plans[0], CliError(code="x", message="no"), [], [], None, 7)

    assert error.recovery_commands == []
    assert error.details["unfiltered_view_id"] is None
