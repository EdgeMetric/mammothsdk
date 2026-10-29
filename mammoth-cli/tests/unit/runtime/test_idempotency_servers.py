"""Servers that honour Idempotency-Key are remembered between commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from mammoth import client as sdk_client

from mammoth_cli.runtime import embedded, idempotency_servers

_SERVER = "https://dev.example/api/v2"


@pytest.fixture(autouse=True)
def _fresh(monkeypatch: pytest.MonkeyPatch, isolated_cli_config: Path) -> None:
    monkeypatch.setattr(sdk_client, "_HONOURS_IDEMPOTENCY", set())


def test_what_one_command_learned_the_next_one_recalls(monkeypatch: pytest.MonkeyPatch) -> None:
    sdk_client.mark_idempotency_keys_honoured(_SERVER)
    idempotency_servers.remember(_SERVER)
    monkeypatch.setattr(sdk_client, "_HONOURS_IDEMPOTENCY", set())
    idempotency_servers.recall(_SERVER)
    assert sdk_client.honours_idempotency_keys(_SERVER)


def test_an_unknown_server_is_not_recalled() -> None:
    idempotency_servers.recall(_SERVER)
    assert not sdk_client.honours_idempotency_keys(_SERVER)


def test_an_embedded_call_never_touches_the_disk(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(embedded, "active", lambda: True)
    sdk_client.mark_idempotency_keys_honoured(_SERVER)
    idempotency_servers.remember(_SERVER)
    assert not idempotency_servers._path().exists()
