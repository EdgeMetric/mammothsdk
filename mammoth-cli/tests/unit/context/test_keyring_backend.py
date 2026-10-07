"""The recorded keyring backend skips keyring's plugin scan on later runs."""

from __future__ import annotations

import json
from pathlib import Path

import keyring
import keyring.backends.null
import pytest

from mammoth_cli.context import keyring_backend


@pytest.fixture
def enabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    monkeypatch.delenv("PYTHON_KEYRING_BACKEND", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setattr(keyring_backend, "_enabled", True)
    monkeypatch.setattr(keyring_backend, "_recorded", False)
    return keyring_backend._cache_path()


def test_remember_then_install_selects_the_recorded_backend(enabled: Path) -> None:
    keyring_backend.remember(keyring.backends.null.Keyring())
    assert json.loads(enabled.read_text())["backend"] == "keyring.backends.null:Keyring"

    keyring_backend._recorded = False
    keyring_backend.install_cached()
    assert type(keyring.get_keyring()) is keyring.backends.null.Keyring


def test_a_stale_record_is_a_miss(enabled: Path) -> None:
    enabled.parent.mkdir(parents=True, exist_ok=True)
    enabled.write_text(json.dumps({"backend": "gone.module:Keyring", "keyring": "0"}))
    before = keyring.get_keyring()
    keyring_backend.install_cached()
    assert keyring.get_keyring() is before


def test_an_explicit_backend_choice_is_never_cached(
    enabled: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYTHON_KEYRING_BACKEND", "keyring.backends.null.Keyring")
    keyring_backend.remember(keyring.backends.null.Keyring())
    assert not enabled.exists()


def test_disabled_by_default_for_library_callers(
    enabled: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(keyring_backend, "_enabled", False)
    keyring_backend.remember(keyring.backends.null.Keyring())
    assert not enabled.exists()
