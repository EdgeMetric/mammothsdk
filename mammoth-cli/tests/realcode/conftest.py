"""Isolation fixtures for the real-code suite.

Real-code tests drive the genuine CLI stack in-process with only the HTTP
socket faked. Authentication requires a login (there is no environment
credential path), so every test runs against a disposable config directory and
in-memory keyring with a default profile already logged in.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import keyring
import keyring.backend
import keyring.errors
import pytest

from mammoth_cli.testing import login_default_profile


class _MemoryKeyring(keyring.backend.KeyringBackend):
    """An in-process keyring backend so tests never touch the real OS keyring."""

    priority = 1  # type: ignore[assignment]

    def __init__(self) -> None:
        super().__init__()
        self._store: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self._store.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self._store[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        try:
            del self._store[(service, username)]
        except KeyError as exc:
            raise keyring.errors.PasswordDeleteError(str((service, username))) from exc


@pytest.fixture(autouse=True)
def _isolated_keyring() -> None:
    """Install a fresh in-memory keyring for every real-code test."""
    keyring.set_keyring(_MemoryKeyring())


@pytest.fixture(autouse=True)
def isolated_cli_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the CLI's non-secret config directory to a disposable tmp_path."""

    def _fake_user_config_dir(*_args: Any, **_kwargs: Any) -> str:
        return str(tmp_path)

    monkeypatch.setattr(
        "mammoth_cli.context.profiles.platformdirs.user_config_dir", _fake_user_config_dir
    )
    return tmp_path


@pytest.fixture(autouse=True)
def _logged_in(isolated_cli_config: Path) -> None:
    """Log in a default profile so in-process CLI invocations authenticate."""
    login_default_profile()
