"""Subprocess tests: malformed auth input yields a stable envelope, not a traceback.

These run the real ``mammoth`` entry point in machine mode and assert that a
nonnumeric workspace id and malformed JSON/YAML each produce the versioned
error envelope with the usage exit code (2) — never a Python traceback.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from mammoth_cli.context.resolver import (
    ENV_API_KEY,
    ENV_API_SECRET,
    ENV_SERVER_PREFIX,
    ENV_WORKSPACE_ID,
)

pytestmark = pytest.mark.subprocess

_EXIT_USAGE = 2
_MAMMOTH_ENV = (
    ENV_API_KEY,
    ENV_API_SECRET,
    ENV_WORKSPACE_ID,
    ENV_SERVER_PREFIX,
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


def test_nonnumeric_workspace_id_is_a_clean_envelope() -> None:
    """A nonnumeric MAMMOTH_WORKSPACE_ID maps to a usage-error envelope."""
    env = _base_env()
    env[ENV_API_KEY] = "k"
    env[ENV_API_SECRET] = "s"
    env[ENV_WORKSPACE_ID] = "abc"

    result = _run(["auth", "login", "--from-env", "--output", "json", "--no-input"], env=env)

    assert result.returncode == _EXIT_USAGE, result.stderr
    assert "Traceback" not in result.stderr
    payload = json.loads(result.stdout or result.stderr)
    assert payload["error"]["code"] == "invalid_workspace_id"


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
