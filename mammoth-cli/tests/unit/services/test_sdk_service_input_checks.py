"""The checks the SDK service makes on a call before anything is sent.

Contract (docstrings in ``mammoth_cli/services/sdk_service.py``): agent-facing inputs name columns
by display name only, never by the backend's internal id; a numeric-looking string compared with a
NUMERIC column is converted (or refused locally) because the backend would put the pipeline into
``ref_error``; a 403 is only "not a member" when the member-only project list lacks the project;
the SDK's expression parser reports a position, and the name that failed is read from there.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest
from mammoth.exceptions import MammothAPIError

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services import sdk_service as sdk
from mammoth_cli.services.sdk_service import SdkMammothService

AUTH = ResolvedAuth(
    api_key="key",
    api_secret="secret",
    workspace_id=4,
    base_url="https://unused.invalid/api/v2",
)


class View:
    """What the checks read of a hydrated view: display name to internal name, and types."""

    def __init__(self, columns: dict[str, str], types: dict[str, str] | None = None) -> None:
        self.columns = columns
        self.column_types = types or {}
        self.display_names: list[str] = []


SALES = View(
    {"Region": "column_aaa111", "Amount": "column_bbb222", "Order date": "column_ccc333"},
    {"Region": "TEXT", "Amount": "NUMERIC", "Order date": "DATE"},
)


def _reject(view: View, method: str = "filter_rows", **kwargs: Any) -> None:
    SdkMammothService._reject_internal_column_inputs(view, method, kwargs)


def _refusal(view: View, method: str = "filter_rows", **kwargs: Any) -> CliError:
    with pytest.raises(CliError) as excinfo:
        _reject(view, method, **kwargs)
    assert excinfo.value.exit_status == 2
    return excinfo.value


# ── display names only ──


def test_display_names_are_accepted_in_every_column_slot() -> None:
    _reject(
        SALES,
        column="Region",
        columns=["Region", "Amount"],
        group_by=["Region"],
        partition_by=["Region"],
        column_mapping={"Region": "Area"},  # the destination label is the caller's own
    )


def test_a_backend_column_id_is_refused_and_the_display_name_suggested() -> None:
    error = _refusal(SALES, column="column_bbb222")
    assert error.code == "internal_column_name"
    assert error.message.startswith("column_bbb222 must use a display name, not an internal")
    assert error.details["reference"] == "column_bbb222"
    assert error.details["scope"] == "column"
    assert error.details["available"] == ["Amount", "Order date", "Region"]


def test_an_unknown_name_is_refused_with_the_nearest_display_name() -> None:
    error = _refusal(SALES, column="Regon")
    assert error.code == "unknown_column"
    assert error.message == (
        "Column reference 'Regon' is not a display name in this view. Did you mean 'Region'?"
    )
    assert error.details["did_you_mean"] == "Region"
    assert "case-sensitive" in (error.hint or "")


def test_a_name_far_from_every_column_gets_no_suggestion() -> None:
    error = _refusal(SALES, column="zzzzzzzz")
    assert error.message == "Column reference 'zzzzzzzz' is not a display name in this view."
    assert error.details["did_you_mean"] is None
    assert error.hint == "Use one of the available display names from view metadata."


def test_a_name_inside_a_list_is_reported_with_its_position() -> None:
    error = _refusal(SALES, columns=["Region", "Nope"])
    assert error.details["scope"] == "columns[1]"


def test_a_display_name_that_equals_an_internal_id_is_a_display_name() -> None:
    view = View({"column_x": "column_x"})
    _reject(view, column="column_x")


def test_a_non_string_value_is_not_a_column_reference() -> None:
    _reject(SALES, column=5, columns=[7])


def test_the_column_mapping_checks_its_source_keys_only() -> None:
    error = _refusal(SALES, column_mapping={"Missing": "Anything"})
    assert error.details["scope"] == "column_mapping"


# ── expressions ──


def test_an_expression_naming_a_backend_id_is_refused() -> None:
    error = _refusal(SALES, "math", expression="Amount * column_bbb222")
    assert error.code == "internal_column_name"
    assert error.details["scope"] == "expression"
    assert error.details["reference"] == "column_bbb222"


def test_an_expression_of_display_names_with_spaces_passes() -> None:
    _reject(SALES, "math", expression="Amount * 2 + Order date")


def test_an_internal_id_that_is_only_the_start_of_a_longer_word_is_not_a_reference() -> None:
    _reject(SALES, "math", expression="Amount + column_bbb222_total")


def test_the_longest_display_name_wins_over_a_shorter_one_that_prefixes_it() -> None:
    view = View({"Total": "column_t1", "Total tax": "column_t2"})
    _reject(view, "math", expression="Total tax - Total")


# ── conditions ──


def test_a_condition_column_must_be_a_display_name_at_any_depth() -> None:
    condition = {
        "and": [
            {"column": "Region", "operator": "=", "value": "N"},
            {"not": {"or": [{"column": "column_bbb222", "operator": ">", "value": 1}]}},
        ]
    }
    error = _refusal(SALES, condition=condition)
    assert error.code == "internal_column_name"
    assert error.details["scope"] == "condition.column"


def test_a_column_to_column_comparison_checks_the_value_as_a_column_too() -> None:
    ok = {"column": "Amount", "operator": ">", "value": "Amount", "value_is_column": True}
    _reject(SALES, condition=ok)
    bad = {"column": "Amount", "operator": ">", "value": "Nope", "value_is_column": True}
    assert _refusal(SALES, condition=bad).details["scope"] == "condition.value"


def test_a_number_written_as_text_is_converted_for_a_number_column_in_place() -> None:
    leaf: dict[str, Any] = {"column": "Amount", "operator": ">", "value": "1000"}
    _reject(SALES, condition={"or": [leaf]})
    assert leaf["value"] == 1000
    assert isinstance(leaf["value"], int)


# ── join and lookup ──


def test_a_join_checks_each_side_against_its_own_view() -> None:
    other = View({"Id": "column_i", "Name": "column_n"})
    _reject(
        SALES,
        "join",
        foreign_view=other,
        on=[{"left": "Region", "right": "Id"}],
        select=["Name", {"column": "Id"}],
    )
    left_bad = _refusal(
        SALES, "join", foreign_view=other, on=[{"left": "Id", "right": "Id"}], select=[]
    )
    assert left_bad.details["scope"] == "on.left"
    right_bad = _refusal(
        SALES, "join", foreign_view=other, on=[{"left": "Region", "right": "Region"}], select=[]
    )
    assert right_bad.details["scope"] == "on.right"
    select_bad = _refusal(SALES, "join", foreign_view=other, on=[], select=["Region"])
    assert select_bad.details["scope"] == "select"


def test_a_lookup_checks_its_key_and_value_against_the_lookup_view() -> None:
    other = View({"Code": "column_c", "Label": "column_l"})
    _reject(SALES, "lookup", lookup_view_id=other, key="Code", value="Label")
    assert (
        _refusal(SALES, "lookup", lookup_view_id=other, key="Region", value="Label").details[
            "scope"
        ]
        == "key"
    )
    assert (
        _refusal(SALES, "lookup", lookup_view_id=other, key="Code", value="Amount").details["scope"]
        == "value"
    )


# ── numeric condition values ──


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("42", 42),
        ("-7", -7),
        ("3.5", 3.5),
        ("2.0", 2),
        (["1", "2.5", 3, "4.0"], [1, 2.5, 3, 4]),
        (9, 9),
    ],
)
def test_numeric_text_is_converted_for_a_number_column(given: Any, expected: Any) -> None:
    spec = {"column": "Amount", "value": given}
    SdkMammothService.coerce_numeric_condition_value(spec, {"Amount": "NUMERIC"})
    assert spec["value"] == expected


@pytest.mark.parametrize("column_type", ["TEXT", "DATE", None])
def test_other_column_types_keep_their_value(column_type: str | None) -> None:
    spec = {"column": "Amount", "value": "2026-01-01"}
    types = {} if column_type is None else {"Amount": column_type}
    SdkMammothService.coerce_numeric_condition_value(spec, types)
    assert spec["value"] == "2026-01-01"


def test_text_that_is_no_number_is_refused_locally_for_a_number_column() -> None:
    spec = {"column": "Amount", "value": ["1", "N/A"]}
    with pytest.raises(CliError) as excinfo:
        SdkMammothService.coerce_numeric_condition_value(spec, {"Amount": "NUMERIC"})
    assert excinfo.value.code == "invalid_condition_value"
    assert excinfo.value.exit_status == 2
    assert excinfo.value.message == (
        "Condition value 'N/A' for column 'Amount' (NUMERIC) is not a valid number."
    )
    assert excinfo.value.details == {
        "column": "Amount",
        "column_type": "NUMERIC",
        "value": "N/A",
    }


def test_a_condition_spec_without_a_column_name_is_left_alone() -> None:
    spec: dict[str, Any] = {"value": "x"}
    SdkMammothService.coerce_numeric_condition_value(spec, {"Amount": "NUMERIC"})
    assert spec == {"value": "x"}


# ── expression parser errors ──


@pytest.mark.parametrize(
    ("message", "expression", "token"),
    [
        ("Unrecognized token at position 9", "Amount + Total tax * 2", "Total tax"),
        ("Unrecognized token at position 0", "Mystery", "Mystery"),
        ("Unrecognized token at position 5", "A + (B)", "B"),
        ("Unrecognized token at position 4", "A + (B)", "A + (B)"),
        ("Unrecognized token at position 7", "Amount ", "Amount "),
        ("something else", "Amount + 1", "Amount + 1"),
        ("Unrecognized token at position 3", 42, "42"),
    ],
)
def test_the_name_the_parser_stopped_at_is_read_from_its_position(
    message: str, expression: Any, token: str
) -> None:
    assert sdk._unrecognized_expression_token(message, expression) == token


# ── signature misfit ──


def test_a_call_with_the_wrong_fields_is_told_apart_from_a_fault_inside_the_sdk() -> None:
    def method(a: int, b: int = 0) -> int:
        return a + b

    assert sdk._signature_misfit(method, {"a": 1}) is None
    assert sdk._signature_misfit(method, {"a": 1, "b": 2}) is None
    assert "missing a required argument: 'a'" in (sdk._signature_misfit(method, {}) or "")
    assert "unexpected keyword argument 'c'" in (
        sdk._signature_misfit(method, {"a": 1, "c": 3}) or ""
    )


# ── settle all ──


def test_every_read_is_settled_and_a_failure_is_its_own_result_not_the_whole_batch() -> None:
    async def ok(value: int) -> int:
        return value

    async def boom() -> int:
        raise ValueError("no")

    results = asyncio.run(sdk._settle_all([ok(1), boom(), 7, ok(3)]))
    assert results[0] == 1
    assert isinstance(results[1], ValueError) and str(results[1]) == "no"
    assert results[2:] == [7, 3]


def test_no_more_than_eight_reads_run_at_once() -> None:
    running = 0
    peak = 0

    async def work() -> None:
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        running -= 1

    asyncio.run(sdk._settle_all([work() for _ in range(20)]))
    assert peak == 8


# ── columns a later batch step can see ──


def test_columns_a_built_step_adds_are_visible_to_the_next_step() -> None:
    view = View({"A": "column_a"}, {"A": "TEXT"})
    view.display_names = ["A"]
    sdk.add_columns_to_view(
        view,
        [
            {"COLUMN": "Total", "INTERNAL_NAME": "column_t", "TYPE": "NUMERIC"},
            {"COLUMN": "Note", "INTERNAL_NAME": "column_n", "TYPE": "TEXT"},
        ],
    )
    assert view.columns == {"A": "column_a", "Total": "column_t", "Note": "column_n"}
    assert view.column_types == {"A": "TEXT", "Total": "NUMERIC", "Note": "TEXT"}
    assert view.display_names == ["A", "Total", "Note"]


# ── error mapping that needs the client ──


@pytest.fixture
def service() -> Iterator[SdkMammothService]:
    instance = SdkMammothService(AUTH)
    real_client = instance._client
    try:
        yield instance
    finally:
        instance._client = real_client
        instance.close()


def test_a_project_that_is_not_in_the_listing_is_a_not_found_naming_only_the_asked_id(
    service: SdkMammothService,
) -> None:
    exc = ValueError("Project ID 5 not found. Available: 1, 2, 3")
    error = service._project_miss_error(exc, 5)
    assert error is not None
    assert error.code == "resource_not_found"
    assert error.exit_status == 5
    assert error.message == "Project 5 was not found in workspace 4."
    assert error.details == {"project_id": 5, "workspace_id": 4}
    assert error.recovery_commands == ["mammoth project list"]
    quoted = service._project_miss_error(ValueError("Project 'Sales' not found. x"), "Sales")
    assert quoted is not None and quoted.message == "Project Sales was not found in workspace 4."


def test_any_other_value_error_is_not_a_project_miss(service: SdkMammothService) -> None:
    assert service._project_miss_error(ValueError("bad value"), 5) is None


def test_a_view_in_no_dataset_is_a_not_found_naming_the_project_searched(
    service: SdkMammothService, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(service, "_client", SimpleNamespace(project_id=180))
    error = service._discovery_miss_error(ValueError("View 7 not found in any dataset"), 7)
    assert error is not None
    assert error.code == "resource_not_found"
    assert error.message == (
        "View 7 was not found in any dataset of project 180; "
        "parent discovery walked every visible dataset and folder."
    )
    assert error.details["view_id"] == 7
    assert error.details["project_id"] == 180
    assert error.recovery_commands == [
        "mammoth dataset list --project 180",
        "mammoth dataset find NAME_SUBSTRING",
    ]
    assert service._discovery_miss_error(ValueError("other"), 7) is None


class _Forbidden(MammothAPIError):
    def __init__(self) -> None:
        super().__init__("forbidden", status_code=403)


def test_a_403_is_not_a_member_error_only_when_the_member_list_lacks_the_project(
    service: SdkMammothService, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def listing() -> list[dict[str, int]]:
        return [{"id": 1}, {"id": 2}]

    monkeypatch.setattr(
        service, "_client", SimpleNamespace(projects=SimpleNamespace(list_all=listing))
    )
    assert service._non_member_project(_Forbidden(), {"project_id": 9}) == 9
    assert service._non_member_project(_Forbidden(), {"project_id": 2}) is None


def test_a_403_with_no_project_or_another_error_has_no_non_member_project(
    service: SdkMammothService,
) -> None:
    assert service._non_member_project(_Forbidden(), {}) is None
    assert service._non_member_project(ValueError("x"), {"project_id": 9}) is None
    other = MammothAPIError("server", status_code=500)
    assert service._non_member_project(other, {"project_id": 9}) is None


def test_the_member_list_failing_leaves_the_error_unchanged(
    service: SdkMammothService, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def listing() -> list[dict[str, int]]:
        raise MammothAPIError("down", status_code=500)

    monkeypatch.setattr(
        service, "_client", SimpleNamespace(projects=SimpleNamespace(list_all=listing))
    )
    assert service._non_member_project(_Forbidden(), {"project_id": 9}) is None
