"""Live: ``doctor``'s ``server`` check reaches the real API v2 ``/health`` with no login at all."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.live


def test_server_check_reports_the_release_server_even_when_auth_fails(tmp_path: Path) -> None:
    env = dict(os.environ)
    env.update(
        HOME=str(tmp_path),
        XDG_CONFIG_HOME=str(tmp_path / "config"),
        XDG_STATE_HOME=str(tmp_path / "state"),
        XDG_CACHE_HOME=str(tmp_path / "cache"),
        MAMMOTH_NO_UPDATE_CHECK="1",
        MAMMOTH_SERVER_PREFIX=os.environ.get("MAMMOTH_SERVER_PREFIX") or "release",
    )
    env.pop("MAMMOTH_API_TOKEN", None)
    result = subprocess.run(
        [sys.executable, "-m", "mammoth_cli", "doctor", "--output", "json"],
        capture_output=True,
        text=True,
        timeout=90,
        env=env,
    )
    checks = {c["name"]: c for c in json.loads(result.stdout)["data"]["checks"]}
    assert checks["credentials"]["ok"] is False  # auth failed ...
    assert checks["server"]["ok"] is True  # ... and the server is still told apart
    assert checks["server"]["status_code"] == 200
