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
    assert "more than one plausible way to be read" in health[0]["detail"]
    assert "delimiter" not in health[0]["detail"]
    assert health[0]["fix"].startswith("mammoth dataset get 2759")


def test_the_backends_stored_suggestion_is_quoted_not_replaced_by_a_guess() -> None:
    data = {
        "id": 3108,
        "status": "has_unstructured_data",
        "additional_info": {
            "interpretation": {
                "reasons": ["no header candidates but first_data_row=4"],
                "instruction_suggestions": ["Skip preamble rows, row 5 is the header"],
            }
        },
    }

    entry = with_dataset_health(data)["dataset_health"][0]

    assert entry["stored_suggestions"] == ["Skip preamble rows, row 5 is the header"]
    assert "no header candidates but first_data_row=4" in entry["detail"]
    assert "delimiter" not in entry["detail"]
    assert entry["fix"].startswith("mammoth dataset interpretation preview 3108 --input ")
    assert "Skip preamble rows, row 5 is the header" in entry["fix"]


def test_a_job_result_names_its_dataset_ds_id_and_still_carries_the_health() -> None:
    # `job get` answers {"job": {"response": {"ds_id": 3108, "status": ...}}}: no "id" key.
    data = {
        "job": {"status": "success", "response": {"ds_id": 3108, "status": "has_unstructured_data"}}
    }

    health = with_dataset_health(data)["dataset_health"]

    assert [h["dataset_id"] for h in health] == [3108]


def test_datasets_in_a_listing_are_checked_too() -> None:
    data = {
        "datasets": [
            {"id": 1, "name": "ok.csv", "status": "ready"},
            {"id": 2, "name": "bad.csv", "status": "has_unstructured_data"},
        ]
    }

    health = with_dataset_health(data)["dataset_health"]

    assert [(h["dataset_id"], h["health"]) for h in health] == [(1, "healthy"), (2, "unhealthy")]


def test_a_listed_dataset_with_an_unclassified_status_is_unknown_not_silent() -> None:
    data = {"datasets": [{"id": 5, "name": "x.csv", "status": "processing"}, {"id": 6}]}

    health = with_dataset_health(data)["dataset_health"]

    assert [(h["dataset_id"], h["health"]) for h in health] == [(5, "unknown"), (6, "unknown")]
    assert "processing" in health[0]["detail"]


def test_a_dataset_get_result_says_healthy() -> None:
    health = with_dataset_health({"dataset": {"id": 1, "status": "ready"}})["dataset_health"]

    assert health[0]["health"] == "healthy"


def test_healthy_results_are_left_exactly_as_they_were() -> None:
    data = {"id": 1, "name": "ok.csv", "status": "ready"}

    assert with_dataset_health(data) is data
    assert with_dataset_health(["not", "a", "dict"]) == ["not", "a", "dict"]


def test_a_dataset_get_record_in_need_action_quotes_the_backends_own_words() -> None:
    # Shape of `dataset get` after the backend maps has_unstructured_data to need_action:
    # status_info["need_action"] carries the text with "Suggested: ..." appended.
    data = {
        "id": 3108,
        "name": "wb.csv",
        "status": "need_action",
        "status_info": {
            "need_action": (
                "This file has more than one plausible way to be read. "
                "Suggested: Skip preamble rows, row 5 is the header"
            )
        },
        "additional_info": {
            "interpretation": {
                "instruction_suggestions": ["Skip preamble rows, row 5 is the header"]
            }
        },
    }

    entry = with_dataset_health(data)["dataset_health"][0]

    assert entry["status"] == "need_action"
    assert "needs a user decision" in entry["detail"]
    assert "Suggested: Skip preamble rows, row 5 is the header" in entry["detail"]
    assert "delimiter" not in entry["detail"]
    assert entry["fix"].startswith("mammoth dataset interpretation preview 3108 --input ")
