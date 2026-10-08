"""Live: ``connector list`` reports a connector the plan includes as available.

The in-product agent told a user SFTP was "premium, not enabled in this
workspace" because the CLI inferred that from ``is_premium and not is_added``.
The server now reports ``is_available`` (the check that gates creating a
connection) and the CLI trusts it::

    pytest tests/live/test_connector_availability.py -m live -v
"""

from __future__ import annotations

import pytest
from live_harness import LiveCli

pytestmark = pytest.mark.live


def test_sftp_is_available_in_a_workspace_whose_plan_includes_it(live_cli: LiveCli) -> None:
    """koyal workspace 4 can create SFTP connections, so `connector list` must not say otherwise."""
    connectors, _ = live_cli.ok("connector", "list")
    sftp = next(c for c in connectors if c["name_key"] == "sftp")
    assert sftp["is_available"] is True
    assert "availability" not in sftp


def test_connector_get_reports_the_same_availability_as_list(live_cli: LiveCli) -> None:
    """`connector get sftp` must carry the plan check too, not just the premium catalogue flag."""
    sftp, _ = live_cli.ok("connector", "get", "sftp")
    assert sftp["is_available"] is True
    assert "availability" not in sftp
