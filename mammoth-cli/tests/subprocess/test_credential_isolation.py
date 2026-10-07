"""Guard: a test's child processes can never reach the developer's real credentials.

Subprocess tests build their environment from ``os.environ``. A child ignores the
in-process keyring a fixture installs, so unless the environment itself has no
D-Bus session and a failing keyring backend, a fuzzed ``auth login``/``logout``
reaches the real SecretService keyring and the real config directory.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.fuzz import harness

pytestmark = pytest.mark.subprocess

_PROBE = (
    "import keyring, platformdirs;"
    "print(type(keyring.get_keyring()).__module__, platformdirs.user_config_dir('x'))"
)


def _probe(env: dict[str, str]) -> tuple[str, str]:
    done = subprocess.run(
        [sys.executable, "-c", _PROBE], capture_output=True, text=True, env=env, timeout=60
    )
    backend, config = done.stdout.split()
    return backend, config


def test_test_environment_has_no_dbus_and_a_failing_keyring(tmp_path: Path) -> None:
    assert "DBUS_SESSION_BUS_ADDRESS" not in os.environ
    backend, config = _probe(dict(os.environ))
    assert backend == "keyring.backends.fail"
    assert Path(config).is_relative_to(tmp_path)


def test_fuzz_child_environment_has_no_dbus_and_a_failing_keyring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A developer shell: a live D-Bus session and no keyring override.
    monkeypatch.setenv("DBUS_SESSION_BUS_ADDRESS", "unix:path=/run/user/1000/bus")
    monkeypatch.delenv("PYTHON_KEYRING_BACKEND")
    env = harness.child_env(tmp_path / "fuzz-home")
    assert "DBUS_SESSION_BUS_ADDRESS" not in env
    assert env["PYTHON_KEYRING_BACKEND"] == "keyring.backends.fail.Keyring"
    backend, config = _probe(env)
    assert backend == "keyring.backends.fail"
    assert Path(config).is_relative_to(tmp_path)
