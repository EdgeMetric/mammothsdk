"""Live: ``view export live-link`` creates a public link flagged ``liveLink`` and returns its URL.

A real view in a scratch project; the export the server stored is read back. Run on the
box with the test identity (see ``conftest.py``)::

    pytest tests/live/test_view_export_live_link.py -m live -v
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from live_harness import LiveCli, SalesData

pytestmark = pytest.mark.live


def _live_link(live_cli: LiveCli, sales: SalesData, **document: Any) -> dict[str, Any]:
    return live_cli.run(
        *("view", "export", "live-link", str(sales.view), str(sales.dataset)),
        *("--input", json.dumps(document), "--yes"),
        project=sales.project,
    )


def _stored_export(live_cli: LiveCli, sales: SalesData, url: str) -> dict[str, Any]:
    listed, _ = live_cli.ok(
        *("view", "export", "list", str(sales.view), str(sales.dataset)), project=sales.project
    )
    file_name = url.rsplit("/", 1)[-1]
    (found,) = [e for e in listed["exports"] if file_name in json.dumps(e)]
    return dict(found)


def test_live_link_returns_the_url_of_a_flagged_s3_export(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    envelope = _live_link(live_cli, sales_data, file_name="report_Ab12Cd34Ef56Gh78.csv")

    assert "error" not in envelope, envelope
    url = envelope["data"]["url"]
    assert url.startswith("https://") and url.endswith(".csv")
    stored = _stored_export(live_cli, sales_data, url)
    assert stored["handler_type"] == "s3"
    assert stored["additional_properties"]["liveLink"] is True
    assert stored["target_properties"]["file"].startswith("report_")


def test_a_caller_additional_property_is_kept_next_to_the_live_link_flag(
    live_cli: LiveCli, sales_data: SalesData
) -> None:
    envelope = _live_link(live_cli, sales_data, additional_properties={"note": "q3"})

    assert "error" not in envelope, envelope
    stored = _stored_export(live_cli, sales_data, envelope["data"]["url"])
    assert stored["additional_properties"] == {"note": "q3", "liveLink": True}
