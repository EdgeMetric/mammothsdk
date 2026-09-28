"""A dataset that did not load cleanly says so in every result that shows it.

A file whose rows could not be split into columns (a wrong quote character)
loads with status ``has_unstructured_data`` and no usable rows. The agent read
the dataset, saw nothing wrong, and answered from an empty table (koyal QA
2026-09-28, book3). The status was in the output; nothing said what it meant.
"""

from __future__ import annotations

from mammoth_cli.runtime.dataset_health import with_dataset_health


def test_a_dataset_that_loaded_badly_carries_its_health_and_fix() -> None:
    data = {"id": 2759, "name": "book3.csv", "status": "has_unstructured_data"}

    health = with_dataset_health(data)["dataset_health"]

    assert [h["dataset_id"] for h in health] == [2759]
    assert "could not be split into columns" in health[0]["detail"]
    assert health[0]["fix"].startswith("mammoth dataset broken-rows list 2759")


def test_datasets_in_a_listing_are_checked_too() -> None:
    data = {
        "datasets": [
            {"id": 1, "name": "ok.csv", "status": "ready"},
            {"id": 2, "name": "bad.csv", "status": "has_unstructured_data"},
        ]
    }

    health = with_dataset_health(data)["dataset_health"]

    assert [h["dataset_id"] for h in health] == [2]


def test_healthy_results_are_left_exactly_as_they_were() -> None:
    data = {"id": 1, "name": "ok.csv", "status": "ready"}

    assert with_dataset_health(data) is data
    assert with_dataset_health(["not", "a", "dict"]) == ["not", "a", "dict"]
