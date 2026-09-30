"""List summaries carry what tells items apart and fit the agent output cap."""

from __future__ import annotations

from typing import Any

from mammoth_cli.services import listing

_NAMES = ["Order ID", "Order Date", "Ship Mode", "Customer", "Region", "Sales", "Profit"]


def _dataset(index: int, columns: int = 21, source: str = "file") -> dict[str, Any]:
    return {
        "id": 3000 + index,
        "name": f"Superstore orders v{index}",
        "status": "ready",
        "created_at": "2026-09-27T14:03:11.532945Z",
        "updated_at": "2026-09-28T09:10:00Z",
        "stats": {"row_count": 9994, "column_count": columns, "batch_count": 1, "size": 1000},
        "sources": [{"type": source, "details": {"file_name": "superstore.csv"}}],
        "data_schema": [
            {"c_id": f"column_{i}", "c_name": _NAMES[i % len(_NAMES)], "c_type": "text"}
            for i in range(columns)
        ],
    }


def _view(index: int) -> dict[str, Any]:
    return {
        "id": 3600 + index,
        "name": "View 1",
        "ds_id": 3000 + index,
        "row_count": 9994,
        "column_count": 21,
        "created_at": "2026-09-27T14:03:11Z",
        "updated_at": "2026-09-27T14:05:00Z",
        "metadata": [
            {
                "internal_name": f"column_{i}",
                "display_name": _NAMES[i % len(_NAMES)],
                "type": "TEXT",
            }
            for i in range(21)
        ],
    }


def test_a_dataset_summary_says_size_times_source_and_columns() -> None:
    summary = listing.dataset_summary(_dataset(1))
    assert (summary["rows"], summary["cols"]) == (9994, 21)
    assert summary["created"] == "2026-09-27T14:03"
    assert summary["updated"] == "2026-09-28T09:10"
    assert summary["source"] == "file: superstore.csv"
    assert summary["columns"].startswith("Order ID:text, Order Date:text")
    assert "(+17 more)" in summary["columns"]


def test_two_near_duplicate_datasets_are_told_apart_by_their_summaries() -> None:
    first = listing.dataset_summary(_dataset(1))
    second = {**_dataset(2), "stats": {"row_count": 9995, "column_count": 22}}
    assert listing.dataset_summary(second)["rows"] != first["rows"]


def test_updated_is_left_out_when_it_equals_created() -> None:
    record = {**_dataset(1), "updated_at": "2026-09-27T14:03:59Z"}
    summary = listing.dataset_summary(record)
    assert summary["created"] == "2026-09-27T14:03"
    assert "updated" not in summary


def test_source_kinds_are_named_from_the_stored_source_type() -> None:
    assert listing.source_of({"sources": [{"type": "cloud", "details": {}}]}) == "connector"
    assert listing.source_of({"sources": [{"type": "sketch", "details": {}}]}).startswith("created")
    assert listing.source_of({"additional_info": {"DATAVIEW_ID": 9}}) == "export of view 9"
    assert listing.source_of({}) == "unknown"


def test_a_view_summary_names_its_dataset() -> None:
    summary = listing.view_summary(_view(1), _dataset(1), 3001)
    assert summary["dataset_name"] == "Superstore orders v1"
    assert summary["dataset_id"] == 3001
    assert summary["source"] == "file: superstore.csv"


def test_fifteen_freshly_uploaded_datasets_fit_the_tool_output_cap() -> None:
    fresh = [{**_dataset(i), "updated_at": "2026-09-27T14:03:11Z"} for i in range(15)]
    kept, omitted = listing.fit_budget([listing.dataset_summary(d) for d in fresh])
    assert omitted == 0
    assert len(kept) == 15
    assert listing.json_size({"datasets": kept}) < 4000


def test_datasets_all_edited_since_creation_still_fit_a_dozen_to_the_cap() -> None:
    summaries = [listing.dataset_summary(_dataset(i)) for i in range(15)]
    kept, omitted = listing.fit_budget(summaries)
    assert len(kept) >= 12
    assert len(kept) + omitted == 15


def test_a_longer_list_is_cut_at_the_budget_and_says_how_many() -> None:
    summaries = [listing.dataset_summary(_dataset(i)) for i in range(60)]
    kept, omitted = listing.fit_budget(summaries)
    assert 0 < len(kept) < 60
    assert len(kept) + omitted == 60
    assert listing.json_size({"datasets": kept}) < 4000


def test_one_oversized_item_is_still_shown() -> None:
    kept, omitted = listing.fit_budget([{"blob": "x" * 9000}])
    assert len(kept) == 1
    assert omitted == 0


_METADATA = [
    {"internal_name": f"column_{i}", "display_name": name}
    for i, name in enumerate(["Order ID", "Order Date", "Region", "Sales", "A", "B", "C", "D"])
]


def _stats(sample: list[object]) -> dict[str, object]:
    """A stats payload in the shape the backend stores it."""
    return {
        "profile": {
            key: {
                "column_name": key,
                "schema_analysis": {"num_unique": 3},
                "statistical_summary": {"data_sample": sample},
            }
            for key in (f"column_{i}" for i in range(8))
        }
    }


def test_sample_values_are_stored_values_for_the_first_columns_only() -> None:
    found = listing.sample_values(
        _stats(["CA-2018-140151-with-a-long-suffix", "b", "c"]), _METADATA
    )
    assert list(found) == ["Order ID", "Order Date", "Region", "Sales", "A", "B"]
    assert found["Order ID"] == ["CA-2018-1401", "b"]


def test_a_column_with_no_stored_sample_is_left_out_not_invented() -> None:
    assert listing.sample_values({"profile": {}}, _METADATA) == {}
    assert listing.sample_values(None, _METADATA) == {}


def test_stored_sample_dicts_show_their_inner_value_not_a_repr() -> None:
    stored = [{"value": "Monday", "count": 3}, {"value": 42}, {"other": 1}]
    found = listing.sample_values(_stats(stored), _METADATA)
    assert found["Order ID"] == ["Monday", "42"]
    assert "{" not in "".join(found["Order ID"])


def test_a_view_summary_lists_every_column_when_asked() -> None:
    truncated = listing.view_summary(_view(1), _dataset(1), 3001)
    assert "(+17 more)" in truncated["columns"]
    full = listing.view_summary(_view(1), _dataset(1), 3001, all_columns=True)
    assert "more)" not in full["columns"]
    assert full["columns"].count(":text") == 21
