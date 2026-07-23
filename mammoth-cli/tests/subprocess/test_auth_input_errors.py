"""Subprocess tests: malformed auth input yields a stable envelope, not a traceback.

These run the real ``mammoth`` entry point in machine mode and assert that a
non-positive workspace id and malformed JSON/YAML each produce the versioned
error envelope with the usage exit code (2) — never a Python traceback.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.subprocess

_EXIT_USAGE = 2
# Any ambient Mammoth credentials are stripped so the subprocess starts from a
# clean, logged-out state. There is no environment credential path; these names
# are cleared purely for test hygiene.
_MAMMOTH_ENV = (
    "MAMMOTH_API_KEY",
    "MAMMOTH_API_SECRET",
    "MAMMOTH_WORKSPACE_ID",
    "MAMMOTH_SERVER_PREFIX",
)


def _run(
    args: list[str], *, env: dict[str, str], stdin: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "mammoth_cli", *args],
        capture_output=True,
        text=True,
        timeout=60,
        input=stdin,
        env=env,
    )


def _base_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in _MAMMOTH_ENV:
        env.pop(key, None)
    return env


def test_non_positive_workspace_id_is_a_clean_envelope() -> None:
    """A non-positive workspace id in the login document maps to a usage error."""
    env = _base_env()

    args = ["auth", "login", "--input", "-", "--input-format", "json"]
    args += ["--output", "json", "--no-input"]
    result = _run(
        args,
        env=env,
        stdin=json.dumps({"api_key": "k", "api_secret": "s", "workspace_id": 0}),
    )

    assert result.returncode == _EXIT_USAGE, result.stderr
    assert "Traceback" not in result.stderr
    payload = json.loads(result.stdout or result.stderr)
    assert payload["error"]["code"] == "invalid_login_document"


def test_malformed_json_input_is_a_clean_envelope() -> None:
    """A malformed JSON login document maps to a usage-error envelope."""
    env = _base_env()

    args = ["auth", "login", "--input", "-", "--input-format", "json"]
    args += ["--output", "json", "--no-input"]
    result = _run(args, env=env, stdin="{ not valid json")

    assert result.returncode == _EXIT_USAGE, result.stderr
    assert "Traceback" not in result.stderr
    payload = json.loads(result.stdout or result.stderr)
    assert payload["error"]["code"] == "invalid_input_document"


def test_malformed_yaml_input_is_a_clean_envelope() -> None:
    """A malformed YAML login document maps to a usage-error envelope."""
    env = _base_env()

    args = ["auth", "login", "--input", "-", "--input-format", "yaml"]
    args += ["--output", "json", "--no-input"]
    result = _run(args, env=env, stdin="key: value:\n  - broken: : :")

    assert result.returncode == _EXIT_USAGE, result.stderr
    assert "Traceback" not in result.stderr
    payload = json.loads(result.stdout or result.stderr)
    assert payload["error"]["code"] == "invalid_input_document"
