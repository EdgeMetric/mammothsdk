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
    assert health[0]["fix"].startswith("mammoth dataset file-settings get 2759")


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
    # No stored report: the interpretation preview answers 4DSET066, so the fix is the
    # file-settings route that resolves need_action.
    assert "interpretation preview" not in entry["fix"]
    assert entry["fix"].startswith("mammoth dataset file-settings get 3108")
    assert '"initial_skip_count":0' in entry["fix"].replace(" ", "")
    assert "Skip preamble rows, row 5 is the header" in entry["stored_suggestions"]


def test_a_stored_interpretation_report_keeps_the_interpretation_route() -> None:
    data = {
        "id": 9,
        "status": "need_action",
        "additional_info": {
            "interpretation": {"report": {"x": 1}, "instruction_suggestions": ["Use row 2"]}
        },
    }

    entry = with_dataset_health(data)["dataset_health"][0]

    assert entry["fix"].startswith("mammoth dataset interpretation preview 9 --input ")
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
    assert all(h["health_reason"] for h in health)
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
    # No stored report: the interpretation preview answers 4DSET066, so the fix is the
    # file-settings route that resolves need_action.
    assert "interpretation preview" not in entry["fix"]
    assert entry["fix"].startswith("mammoth dataset file-settings get 3108")
    assert '"initial_skip_count":0' in entry["fix"].replace(" ", "")
    assert "Skip preamble rows, row 5 is the header" in entry["stored_suggestions"]


def test_a_stored_interpretation_report_keeps_the_interpretation_route() -> None:
    data = {
        "id": 9,
        "status": "need_action",
        "additional_info": {
            "interpretation": {"report": {"x": 1}, "instruction_suggestions": ["Use row 2"]}
        },
    }

    entry = with_dataset_health(data)["dataset_health"][0]

    assert entry["fix"].startswith("mammoth dataset interpretation preview 9 --input ")


def test_a_compact_listing_entry_without_status_is_judged_from_its_size() -> None:
    # `dataset list` drops `status` for a ready dataset; that is not "unknown".
    data = {"datasets": [{"id": 7, "name": "s.csv", "rows": 120, "cols": 4, "columns": "a:text"}]}

    entry = with_dataset_health(data)["dataset_health"][0]

    assert entry["health"] == "healthy"
    assert "120 rows" in entry["detail"]


def test_a_record_with_nothing_to_judge_by_says_why_it_is_unknown() -> None:
    entry = with_dataset_health({"datasets": [{"id": 6, "name": "x"}]})["dataset_health"][0]

    assert entry["health"] == "unknown"
    assert "mammoth dataset get 6" in entry["health_reason"]


def test_health_name_falls_back_to_dataset_name() -> None:
    data = {"id": 3, "dataset_name": "wb.csv", "status": "need_action"}

    assert with_dataset_health(data)["dataset_health"][0]["name"] == "wb.csv"


def test_an_error_status_is_failed_with_the_backends_reason() -> None:
    data = {
        "datasets": [
            {
                "id": 22,
                "name": "empty.csv",
                "status": "error",
                "status_info": {"error": "The file is empty"},
            }
        ]
    }

    entry = with_dataset_health(data)["dataset_health"][0]

    assert entry["health"] == "failed"
    assert "The file is empty" in entry["detail"]
    assert "health_reason" not in entry


def test_a_names_listing_carries_no_health_entry_per_bare_row() -> None:
    data = {"datasets": [{"id": 1, "name": "a.csv"}, {"id": 2, "name": "b.csv"}]}

    assert with_dataset_health(data) == data
