"""Secret credential storage: keyring-first, permission-checked file fallback."""

from __future__ import annotations

import os
import stat
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


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission checks")
def test_file_read_rejects_group_or_other_permissions(isolated_cli_config: Path) -> None:
    credentials.store_credentials("default", "key-1", "secret-1", storage="file")
    path = credentials.credentials_path()
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)

    with pytest.raises(CliError) as excinfo:
        credentials.load_credentials("default")
    assert excinfo.value.code == "insecure_credential_file"
    assert "secret-1" not in str(excinfo.value.to_envelope())

    with pytest.raises(CliError):
        credentials.store_credentials("default", "new-key", "new-secret", storage="file")
    with pytest.raises(CliError):
        credentials.delete_credentials("default")


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission checks")
def test_file_read_rejects_symlink(isolated_cli_config: Path) -> None:
    credentials.store_credentials("default", "key-1", "secret-1", storage="file")
    path = credentials.credentials_path()
    target = path.with_name("other-credentials.toml")
    target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    os.chmod(target, stat.S_IRUSR | stat.S_IWUSR)
    path.unlink()
    path.symlink_to(target)

    with pytest.raises(CliError) as excinfo:
        credentials.load_credentials("default")
    assert excinfo.value.code == "insecure_credential_file"


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission checks")
def test_file_read_rejects_non_regular_file(isolated_cli_config: Path) -> None:
    credentials.store_credentials("default", "key-1", "secret-1", storage="file")
    path = credentials.credentials_path()
    path.unlink()
    path.mkdir()

    with pytest.raises(CliError) as excinfo:
        credentials.load_credentials("default")
    assert excinfo.value.code == "insecure_credential_file"


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission checks")
def test_file_read_rejects_insecure_parent_directory(isolated_cli_config: Path) -> None:
    credentials.store_credentials("default", "key-1", "secret-1", storage="file")
    directory = credentials.credentials_path().parent
    os.chmod(directory, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)

    with pytest.raises(CliError) as excinfo:
        credentials.load_credentials("default")
    assert excinfo.value.code == "insecure_credential_file"


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission checks")
def test_first_file_store_creates_private_directory(
    isolated_cli_config: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = isolated_cli_config / "new-config"
    monkeypatch.setattr(
        "mammoth_cli.context.profiles.platformdirs.user_config_dir",
        lambda *_args, **_kwargs: str(directory),
    )

    credentials.store_credentials("default", "key-1", "secret-1", storage="file")
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert credentials.load_credentials("default") == ("key-1", "secret-1")


def test_keyring_delete_works_without_file_directory(
    isolated_cli_config: Path,
    fake_keyring_available: dict[tuple[str, str], str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory = isolated_cli_config / "missing-config"
    monkeypatch.setattr(
        "mammoth_cli.context.profiles.platformdirs.user_config_dir",
        lambda *_args, **_kwargs: str(directory),
    )
    credentials.store_credentials("default", "key-1", "secret-1", storage="keyring")
    assert credentials.delete_credentials("default") is True
