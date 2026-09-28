"""A dataset made from an uploaded file says how next period's file joins it.

Asked to send a monthly report to a client automatically, the agent refused:
the dataset "comes from a one-time CSV upload, so a monthly schedule would keep
sending the same data" (eval T2-WPP-W9, 2026-09-28). An upload is not one-time
-- the next file appends to the same dataset as a new batch and its views
re-run -- but nothing the agent read said so.
"""

from __future__ import annotations

from mammoth_cli.runtime.new_data import with_new_data_path


def test_a_file_dataset_says_how_the_next_file_joins_it() -> None:
    data = {
        "dataset": {
            "id": 2830,
            "name": "brand_campaigns.csv",
            "sources": [{"type": "file", "details": {"file_name": "brand_campaigns.csv"}}],
        }
    }

    paths = with_new_data_path(data)["new_data"]

    assert [p["dataset_id"] for p in paths] == [2830]
    assert "mammoth file upload FILE --input '{\"append_to_ds_id\": 2830}'" in paths[0]["how"]


def test_a_dataset_fed_by_a_connector_is_left_alone() -> None:
    data = {"dataset": {"id": 7, "name": "crm", "sources": [{"type": "connector"}]}}

    assert "new_data" not in with_new_data_path(data)
