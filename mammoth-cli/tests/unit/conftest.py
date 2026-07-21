"""Shared fixtures for CLI unit tests: isolated config directory and keyring."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import keyring
import keyring.backend
import keyring.errors
import pytest


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
    """Install a fresh in-memory keyring for every unit test.

    Autouse so no test can read from or write to the developer's real OS
    keyring; each test gets an empty, disposable credential store.
    """
    keyring.set_keyring(_MemoryKeyring())


@pytest.fixture
def isolated_cli_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the CLI's non-secret config directory to a disposable tmp_path.

    Patches ``platformdirs.user_config_dir`` (as seen through
    ``mammoth_cli.context.profiles``) so every profile/settings read or write
    in a test lands in an isolated directory instead of the real OS-native
    location.
    """

    def _fake_user_config_dir(*_args: Any, **_kwargs: Any) -> str:
        return str(tmp_path)

    monkeypatch.setattr(
        "mammoth_cli.context.profiles.platformdirs.user_config_dir", _fake_user_config_dir
    )
    return tmp_path
