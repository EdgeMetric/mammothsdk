from unittest.mock import MagicMock

import pytest

from mammoth.api.dashboards import DashboardsAPI
from mammoth.exceptions import MammothValidationError


def test_assess_twb_posts_binary_multipart_and_closes(tmp_path):
    path = tmp_path / "report.twb"
    path.write_bytes(b"twb")
    client = MagicMock()
    client._request_json.return_value = {"source": {}}
    DashboardsAPI(client).assess_twb(path)
    call = client._request_json.call_args.kwargs
    assert call["files"][0][0] == "file"
    assert call["files"][0][1][0] == "report.twb"
    assert call["files"][0][1][2] == "application/octet-stream"
    assert call["files"][0][1][1].closed


def test_assess_pbix_rejects_missing_file_before_request(tmp_path):
    with pytest.raises(MammothValidationError):
        DashboardsAPI(MagicMock()).assess_pbix(tmp_path / "missing.pbix")
