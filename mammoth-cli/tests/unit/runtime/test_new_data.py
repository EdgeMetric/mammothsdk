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


def test_a_dataset_written_by_a_view_export_names_the_export() -> None:
    """Asked to remove a copy made by a view's export, the agent deleted the copied
    dataset and left the export, which writes it again on the next run (eval
    T1-O-10, 2026-09-28). The dataset's additional_info named the export."""
    data = {
        "dataset": {
            "id": 3002,
            "name": "shipped_orders",
            "additional_info": {"DATAVIEW_ID": 3639, "TRIGGER_ID": 279},
        }
    }

    paths = with_new_data_path(data)["new_data"]

    assert [p["dataset_id"] for p in paths] == [3002]
    assert "mammoth view export delete 3639 279" in paths[0]["how"]
