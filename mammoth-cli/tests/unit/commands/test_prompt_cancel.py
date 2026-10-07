"""A prompt ended by Ctrl-C or EOF is a clean cancel, never an api_error.

Drives the real CLI in a real pseudo-terminal: ``upgrade --version`` reaches its
confirm prompt without any network, and ``auth logout`` has a second confirm.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pexpect
import pytest

from mammoth_cli.errors.envelope import EXIT_INTERRUPT


def _spawn(argv: list[str], home: Path) -> pexpect.spawn:
    env = {k: v for k, v in os.environ.items() if not k.startswith("MAMMOTH_")}
    env.pop("DBUS_SESSION_BUS_ADDRESS", None)
    env.pop("DISPLAY", None)
    env.pop("WAYLAND_DISPLAY", None)
    env.update(
        BROWSER="true",
        HOME=str(home),
        XDG_CONFIG_HOME=str(home / "config"),
        XDG_DATA_HOME=str(home / "data"),
        XDG_STATE_HOME=str(home / "state"),
        PYTHON_KEYRING_BACKEND="keyring.backends.fail.Keyring",
        MAMMOTH_NO_UPDATE_CHECK="1",
        MAMMOTH_LOG_DIR=str(home / "log"),
        NO_COLOR="1",
        TERM="dumb",
    )
    return pexpect.spawn(
        sys.executable,
        ["-m", "mammoth_cli", *argv],
        env=env,
        encoding="utf-8",
        timeout=60,
    )


@pytest.mark.parametrize(
    "argv",
    [["upgrade", "--version", "999.0.0"], ["auth", "logout", "--profile", "nobody"]],
    ids=["upgrade", "auth-logout"],
)
@pytest.mark.parametrize("key", ["EOF", "INT"])
def test_prompt_cancel_is_clean(argv: list[str], key: str, tmp_path: Path) -> None:
    child = _spawn(argv, tmp_path)
    child.expect(r"\[[Yy]/[Nn]\]: ")
    child.sendeof() if key == "EOF" else child.sendintr()
    child.expect(pexpect.EOF)
    child.close()
    text = child.before or ""
    assert "failed unexpectedly" not in text and "api_error" not in text, text
    assert "Cancelled" in text, text
    assert child.exitstatus == EXIT_INTERRUPT, text
