"""Subprocess tests: a misspelt flag is reported by name, whatever else is wrong with the call.

Two paths used to lose the flag. A command that is also a group (``browse
resources``) dropped it before the handler ran, so the call ended as
``project_required``. A command with a required argument (``browse resource``)
ended as ``missing_argument``. Neither named the flag. Both now report
``unknown_option`` naming it. The ``exit 0 on an unknown flag`` cases of the
same fuzz family are guarded here too.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.subprocess

_EXIT_USAGE = 2
_BOGUS = "--bogus-flag"


def _run(args: list[str], home: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update(
        HOME=str(home),
        XDG_CONFIG_HOME=str(home / "config"),
        XDG_STATE_HOME=str(home / "state"),
        XDG_CACHE_HOME=str(home / "cache"),
        MAMMOTH_NO_UPDATE_CHECK="1",
        BROWSER="true",
    )
    for key in ("DISPLAY", "WAYLAND_DISPLAY", "MAMMOTH_SERVER_PREFIX"):
        env.pop(key, None)
    return subprocess.run(
        [sys.executable, "-m", "mammoth_cli", *args],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )


@pytest.mark.parametrize(
    "command",
    [
        ["browse", "resources"],  # also a group: used to end as project_required
        ["browse", "resource"],  # a required argument: used to end as missing_argument
        ["connector", "connection", "get"],
        ["connector", "ds-config", "list"],
        ["auth", "status"],
        ["config", "list"],
        ["config", "path"],
        ["context", "project", "clear"],
        ["context", "project", "status"],
    ],
    ids=" ".join,
)
def test_an_unknown_flag_is_named_and_rejected(command: list[str], tmp_path: Path) -> None:
    done = _run([*command, _BOGUS, "--output", "json"], tmp_path)

    assert done.returncode == _EXIT_USAGE, done.stdout + done.stderr
    output = done.stdout + done.stderr
    error = json.loads(output[output.index("{") :])["error"]
    assert error["code"] == "unknown_option"
    assert error["details"]["option"] == _BOGUS
    assert _BOGUS in error["message"]
