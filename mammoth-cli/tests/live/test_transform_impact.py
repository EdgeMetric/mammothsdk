"""Live: a transform's ``--dry-run`` reports what it would change, and writes nothing.

Replaces the fake-socket realcode tests ``test_dry_run_impact``, ``test_math_dry_run``,
``test_join_dry_run_overlap`` (the dry-run test) and ``test_delete_dry_run_dependents`` (the
lookup test). The module uploads two small CSVs of known content into a scratch project
and checks the counts against the rows it wrote.

``donors`` has 9 rows: one exact duplicate (Ada/10/Pune), two Donor+City duplicates once Gift
is ignored (Ada/Pune and Bo/Delhi), one blank Gift (Cy), and two names holding "Acme".
``clean`` has 5 unique rows with no blanks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest
from live_harness import LiveCli, upload_csv

pytestmark = pytest.mark.live

_DONORS = """Donor,Gift,City
Ada,10,Pune
Ada,10,Pune
Bo,20,Delhi
Bo,25,Delhi
Cy,,Pune
Dee,30,Pune
Acme Corp,40,Delhi
Acme Ltd,50,Delhi
Eve,60,Pune
"""
_CLEAN = """Donor,Gift
Fay,1
Gus,2
Hal,3
Ivy,4
Jo,5
"""
_ORDERS = """cust,amount
a,1
a,2
a,3
b,4
"""
_CUSTOMERS = """id,tier
a,gold
"""


@dataclass(frozen=True)
class Data:
    project: int
    donors: tuple[int, int]
    clean: tuple[int, int]
    orders: tuple[int, int]
    customers: tuple[int, int]


@pytest.fixture(scope="module")
def data(live_cli: LiveCli, scratch_project: int, tmp_path_factory: pytest.TempPathFactory) -> Data:
    folder = tmp_path_factory.mktemp("impact")
    made = {
        name: upload_csv(live_cli, scratch_project, folder / f"{name}.csv", text)
        for name, text in (
            ("donors", _DONORS),
            ("clean", _CLEAN),
            ("orders", _ORDERS),
            ("customers", _CUSTOMERS),
        )
    }
    return Data(scratch_project, made["donors"], made["clean"], made["orders"], made["customers"])


def _transform(
    cli: LiveCli,
    data: Data,
    target: tuple[int, int],
    command: str,
    doc: dict[str, Any],
    *flags: str,
) -> dict[str, Any]:
    """Run ``view transform COMMAND`` on ``target`` (dataset, view); return the envelope."""
    dataset, view = target
    document = json.dumps({"dataset_id": dataset, **doc})
    return cli.run(
        *("view", "transform", command, str(view), "--input", document, *flags),
        project=data.project,
    )


def _dry(
    cli: LiveCli,
    data: Data,
    target: tuple[int, int],
    command: str,
    doc: dict[str, Any],
    *flags: str,
) -> dict[str, Any]:
    return _transform(cli, data, target, command, doc, "--dry-run", *flags)


def _impact(envelope: dict[str, Any]) -> dict[str, Any]:
    assert "error" not in envelope, envelope
    assert envelope["data"]["dry_run"] is True
    impact: dict[str, Any] = envelope["data"]["predicted_impact"]
    return impact


def _steps(cli: LiveCli, data: Data, target: tuple[int, int]) -> int:
    dataset, view = target
    analysed, _ = cli.ok("view", "analyze", str(view), str(dataset), project=data.project)
    return int(analysed["steps"])


# -- discard-duplicates ----------------------------------------------------


def test_discard_duplicates_dry_run_with_no_duplicates_is_a_no_op_error(
    live_cli: LiveCli, data: Data
) -> None:
    error = _dry(live_cli, data, data.clean, "discard-duplicates", {})["error"]

    assert error["code"] == "no_op"
    assert "has no exact duplicate rows (5 of 5 checked)" in error["message"]
    assert "nothing to change" in error["message"]


def test_discard_duplicates_dry_run_reports_the_rows_it_would_remove(
    live_cli: LiveCli, data: Data
) -> None:
    impact = _impact(_dry(live_cli, data, data.donors, "discard-duplicates", {}))

    assert impact == {"rows_removed": 1, "row_count": 9, "rows_after": 8, "exact": True}


def test_discard_duplicates_dry_run_honours_ignore_columns(live_cli: LiveCli, data: Data) -> None:
    doc = {"ignore_columns": ["Gift"]}

    impact = _impact(_dry(live_cli, data, data.donors, "discard-duplicates", doc))

    assert impact["rows_removed"] == 2 and impact["rows_after"] == 7


def test_a_real_discard_duplicates_with_none_adds_no_task(live_cli: LiveCli, data: Data) -> None:
    before = _steps(live_cli, data, data.clean)

    envelope = _transform(live_cli, data, data.clean, "discard-duplicates", {}, "--yes")

    assert envelope["data"]["status"] == "no_change"
    assert "No task was added" in envelope["data"]["note"]
    assert _steps(live_cli, data, data.clean) == before


# -- filter ----------------------------------------------------------------

_KEEP_ALL = {"condition": {"column": "Gift", "operator": "GTE", "value": 0}}
_KEEP_30_UP = {"condition": {"column": "Gift", "operator": "GTE", "value": 30}}


def test_filter_that_keeps_every_row_is_a_no_op(live_cli: LiveCli, data: Data) -> None:
    error = _dry(live_cli, data, data.clean, "filter", _KEEP_ALL)["error"]

    assert error["code"] == "no_op" and "keeps all of them" in error["message"]


def test_filter_reports_the_rows_it_would_remove(live_cli: LiveCli, data: Data) -> None:
    impact = _impact(_dry(live_cli, data, data.donors, "filter", _KEEP_30_UP))

    assert impact["rows_after"] == 4 and impact["rows_removed"] == 5


def test_remove_filter_matching_nothing_is_a_no_op_and_matching_some_counts_them(
    live_cli: LiveCli, data: Data
) -> None:
    none = {
        "condition": {"column": "Gift", "operator": "GTE", "value": 1000},
        "filter_type": "REMOVE",
    }
    some = {**_KEEP_30_UP, "filter_type": "REMOVE"}

    assert _dry(live_cli, data, data.donors, "filter", none)["error"]["code"] == "no_op"
    assert _impact(_dry(live_cli, data, data.donors, "filter", some))["rows_removed"] == 4


_NO_SUCH_DONOR = {"condition": {"column": "Donor", "operator": "EQ", "value": "Zed"}}


def test_a_filter_no_row_matches_names_the_values_the_column_holds(
    live_cli: LiveCli, data: Data
) -> None:
    error = _dry(live_cli, data, data.donors, "filter", _NO_SUCH_DONOR)["error"]

    assert error["code"] == "empties_view"
    assert "(0 of 9)" in error["message"]
    assert "Donor holds: " in error["message"] and "Ada (2)" in error["message"]
    assert "--allow-empty" in error["hint"]


def test_a_filter_no_row_matches_passes_its_dry_run_with_allow_empty(
    live_cli: LiveCli, data: Data
) -> None:
    impact = _impact(_dry(live_cli, data, data.donors, "filter", _NO_SUCH_DONOR, "--allow-empty"))

    assert impact["rows_removed"] == 9 and impact["rows_after"] == 0


def test_a_remove_filter_no_row_matches_names_the_values_in_its_no_op(
    live_cli: LiveCli, data: Data
) -> None:
    doc = {**_NO_SUCH_DONOR, "filter_type": "REMOVE"}

    error = _dry(live_cli, data, data.donors, "filter", doc)["error"]

    assert error["code"] == "no_op"
    assert "Donor holds: " in error["message"] and "Ada (2)" in error["message"]


# -- fill-missing, replace, bulk-replace -----------------------------------

_FILL = {"column": "Gift", "direction": "FIRST_VALUE"}


def test_fill_missing_on_a_column_without_blanks_is_a_no_op(live_cli: LiveCli, data: Data) -> None:
    assert _dry(live_cli, data, data.clean, "fill-missing", _FILL)["error"]["code"] == "no_op"


def test_fill_missing_reports_the_blank_cells(live_cli: LiveCli, data: Data) -> None:
    impact = _impact(_dry(live_cli, data, data.donors, "fill-missing", _FILL))

    assert impact["blank_cells"] == 1


def test_replace_of_text_no_row_holds_is_a_no_op_and_text_some_hold_is_counted(
    live_cli: LiveCli, data: Data
) -> None:
    absent = {"columns": ["Donor"], "find": "Zed", "replace": "ZED"}
    present = {"columns": ["Donor"], "find": "acme", "replace": "ACME"}

    assert _dry(live_cli, data, data.donors, "replace", absent)["error"]["code"] == "no_op"
    impact = _impact(_dry(live_cli, data, data.donors, "replace", present))
    assert impact["rows_matching"] == 2


def test_bulk_replace_of_values_no_row_holds_is_a_no_op_and_values_some_hold_are_counted(
    live_cli: LiveCli, data: Data
) -> None:
    absent = {"columns": ["Donor"], "mapping": [{"search": ["Zed", "Yan"], "replace": "c"}]}
    present = {"columns": ["Donor"], "mapping": [{"search": ["Ada", "Bo"], "replace": "c"}]}

    assert _dry(live_cli, data, data.donors, "bulk-replace", absent)["error"]["code"] == "no_op"
    assert _impact(_dry(live_cli, data, data.donors, "bulk-replace", present))["rows_matching"] == 4


def test_replace_scoped_by_a_condition_counts_only_rows_in_scope(
    live_cli: LiveCli, data: Data
) -> None:
    scoped = {
        "columns": ["Donor"],
        "find": "Acme",
        "replace": "ACME",
        "condition": {"column": "Gift", "operator": "GT", "value": 45},
    }
    nothing_in_scope = {**scoped, "condition": {"column": "Gift", "operator": "GT", "value": 500}}

    assert _impact(_dry(live_cli, data, data.donors, "replace", scoped))["rows_matching"] == 1
    error = _dry(live_cli, data, data.donors, "replace", nothing_in_scope)["error"]
    assert error["code"] == "no_op"


# -- join ------------------------------------------------------------------


def test_join_dry_run_reports_match_rate_without_writing(live_cli: LiveCli, data: Data) -> None:
    before = _steps(live_cli, data, data.orders)
    doc = {
        "foreign_view": data.customers[1],
        "foreign_dataset_id": data.customers[0],
        "join_type": "LEFT",
        "on": [{"left": "cust", "right": "id"}],
        "select": ["tier"],
    }

    preview = _dry(live_cli, data, data.orders, "join", doc)["data"]["join_preview"]

    assert preview["checked"] is True, preview
    assert preview["match_rate"] == 0.75
    assert preview["unmatched_keys"] == ["b"]
    assert _steps(live_cli, data, data.orders) == before


# -- math ------------------------------------------------------------------

_BAD_EXPRESSION = 'TRY_CAST(("Gift" AS NUMERIC) * 2)'


def test_dry_run_rejects_an_expression_the_real_run_rejects(live_cli: LiveCli, data: Data) -> None:
    before = _steps(live_cli, data, data.donors)
    doc = {"expression": _BAD_EXPRESSION, "new_column": "out"}

    dry = _dry(live_cli, data, data.donors, "math", doc)["error"]
    real = _transform(live_cli, data, data.donors, "math", doc, "--yes")["error"]

    assert dry["code"] == real["code"] == "unknown_column"
    assert dry["details"] == real["details"]
    assert _steps(live_cli, data, data.donors) == before


def test_dry_run_of_a_valid_expression_stops_without_adding_a_step(
    live_cli: LiveCli, data: Data
) -> None:
    before = _steps(live_cli, data, data.donors)

    envelope = _dry(
        live_cli, data, data.donors, "math", {"expression": '"Gift" * 2', "new_column": "out"}
    )

    assert "error" not in envelope, envelope
    assert envelope["data"]["dry_run"] is True
    assert _steps(live_cli, data, data.donors) == before


# -- dataset delete --------------------------------------------------------


def test_dataset_delete_dry_run_names_the_dataset_and_checks_its_dependents(
    live_cli: LiveCli, data: Data
) -> None:
    dataset = data.donors[0]

    result, _ = live_cli.ok("dataset", "delete", str(dataset), "--dry-run", project=data.project)

    assert result["targets"][0]["id"] == dataset
    assert result["dependents"]["checked"] is True
    assert "dependencies" in result["dependents"]
    again, _ = live_cli.ok("dataset", "get", str(dataset), project=data.project)
    assert again  # a dry run deletes nothing
