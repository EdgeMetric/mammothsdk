"""Subprocess test: ``mammoth doctor`` exits non-zero when its report says ``ok: false``."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.subprocess

_EXIT_AUTH = 4


def test_doctor_without_credentials_prints_report_and_exits_auth(tmp_path: Path) -> None:
    env = dict(os.environ)
    env.update(
        HOME=str(tmp_path),
        XDG_CONFIG_HOME=str(tmp_path / "config"),
        XDG_STATE_HOME=str(tmp_path / "state"),
        XDG_CACHE_HOME=str(tmp_path / "cache"),
        MAMMOTH_NO_UPDATE_CHECK="1",
    )
    for key in ("MAMMOTH_API_TOKEN", "MAMMOTH_SERVER_PREFIX"):
        env.pop(key, None)
    result = subprocess.run(
        [sys.executable, "-m", "mammoth_cli", "doctor", "--output", "json"],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    report = json.loads(result.stdout)
    assert report["data"]["ok"] is False
    assert result.returncode == _EXIT_AUTH
