"""Secret credential storage: keyring-first, permission-checked file fallback."""

from __future__ import annotations

from pathlib import Path

import pytest

from mammoth_cli.context import credentials
from mammoth_cli.errors.envelope import CliError


@pytest.fixture
def fake_keyring_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(credentials, "_keyring_available", lambda: False)


@pytest.fixture
def fake_keyring_available(monkeypatch: pytest.MonkeyPatch) -> dict[tuple[str, str], str]:
    store: dict[tuple[str, str], str] = {}

    def _set(service: str, profile: str, payload: str) -> None:
        store[(service, profile)] = payload

    def _get(service: str, profile: str) -> str | None:
        return store.get((service, profile))

    def _delete(service: str, profile: str) -> None:
        store.pop((service, profile), None)

    monkeypatch.setattr(credentials, "_keyring_available", lambda: True)
    monkeypatch.setattr(credentials.keyring, "set_password", _set)
    monkeypatch.setattr(credentials.keyring, "get_password", _get)
    monkeypatch.setattr(credentials.keyring, "delete_password", _delete)
    return store


def test_store_file_explicit_roundtrip(isolated_cli_config: Path) -> None:
    storage = credentials.store_credentials("default", "key-1", "secret-1", storage="file")
    assert storage == "file"
    assert credentials.load_credentials("default") == ("key-1", "secret-1")
    assert credentials.has_credentials("default")


def test_delete_credentials_file(isolated_cli_config: Path) -> None:
    credentials.store_credentials("default", "key-1", "secret-1", storage="file")
    assert credentials.delete_credentials("default") is True
    assert credentials.load_credentials("default") is None
    assert credentials.delete_credentials("default") is False


def test_auto_storage_noninteractive_without_keyring_fails(
    isolated_cli_config: Path, fake_keyring_unavailable: None
) -> None:
    with pytest.raises(CliError) as excinfo:
        credentials.store_credentials(
            "default", "key-1", "secret-1", storage="auto", interactive=False
        )
    assert excinfo.value.code == "keyring_unavailable"
    assert excinfo.value.exit_status == 2
    assert credentials.load_credentials("default") is None


def test_auto_storage_interactive_without_keyring_uses_file(
    isolated_cli_config: Path, fake_keyring_unavailable: None
) -> None:
    storage = credentials.store_credentials(
        "default", "key-1", "secret-1", storage="auto", interactive=True
    )
    assert storage == "file"
    assert credentials.load_credentials("default") == ("key-1", "secret-1")


def test_keyring_storage_required_but_unavailable_fails(
    isolated_cli_config: Path, fake_keyring_unavailable: None
) -> None:
    with pytest.raises(CliError) as excinfo:
        credentials.store_credentials("default", "key-1", "secret-1", storage="keyring")
    assert excinfo.value.code == "keyring_unavailable"


def test_auto_storage_prefers_keyring_when_available(
    isolated_cli_config: Path, fake_keyring_available: dict[tuple[str, str], str]
) -> None:
    storage = credentials.store_credentials("default", "key-1", "secret-1", storage="auto")
    assert storage == "keyring"
    assert credentials.load_credentials("default") == ("key-1", "secret-1")
    # Nothing was written to the file fallback.
    assert not credentials.credentials_path().exists()


def test_delete_credentials_from_keyring(
    isolated_cli_config: Path, fake_keyring_available: dict[tuple[str, str], str]
) -> None:
    credentials.store_credentials("default", "key-1", "secret-1", storage="keyring")
    assert credentials.delete_credentials("default") is True
    assert credentials.load_credentials("default") is None


def test_error_envelope_never_contains_the_secret(
    isolated_cli_config: Path, fake_keyring_unavailable: None
) -> None:
    try:
        credentials.store_credentials(
            "default", "key-1", "super-secret-value", storage="auto", interactive=False
        )
    except CliError as error:
        assert "super-secret-value" not in str(error.to_envelope())
    else:
        pytest.fail("expected CliError")
