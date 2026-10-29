"""One tool for what an operation, an export destination or an automation task takes."""

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from .helpers import a_fake_api, as_caller, call_tool


def test_an_export_destinations_settings_are_listed() -> None:
    with a_fake_api() as api, as_caller():
        schema = call_tool("get_schema", kind="export", of="sftp")

    assert schema["destination"] == "sftp"
    assert schema["checked"] is True
    assert "host" in schema["required"]
    # Only an automation's schema is Mammoth's to answer.
    assert not api.requests


def test_an_unknown_destination_names_the_ones_there_are() -> None:
    with as_caller(), pytest.raises(ToolError, match="sftp"):
        call_tool("get_schema", kind="export", of="fax")


def test_an_unknown_kind_is_refused() -> None:
    with as_caller(), pytest.raises(ToolError):
        call_tool("get_schema", kind="dashboard", of="board")
