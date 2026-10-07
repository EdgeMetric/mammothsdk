"""No test may be able to open a real browser.

``auth login`` opens the system browser for OAuth. A test that reaches it with a
display and no ``BROWSER`` override opens a window on the developer's desktop.
"""

from __future__ import annotations

import os
import webbrowser
from pathlib import Path

from tests.fuzz import harness


def test_the_test_process_has_no_display_and_a_disabled_browser() -> None:
    assert os.environ.get("BROWSER") == "true"
    assert not os.environ.get("DISPLAY")
    assert not os.environ.get("WAYLAND_DISPLAY")


def test_webbrowser_resolves_to_the_no_op_command() -> None:
    assert webbrowser.get().name == "true"


def test_the_fuzz_child_env_cannot_reach_a_browser(tmp_path: Path) -> None:
    env = harness.child_env(tmp_path / "home")
    assert env["BROWSER"] == "true"
    assert "DISPLAY" not in env and "WAYLAND_DISPLAY" not in env
