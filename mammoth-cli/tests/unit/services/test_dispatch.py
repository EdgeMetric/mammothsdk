"""Unit tests for SDK-symbol method resolution."""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.dispatch import resolve_sdk_method


class ProjectsAPI:
    def list(self, limit: int = 100) -> dict[str, Any]:
        return {"limit": limit}


class _FakeClient:
    def __init__(self) -> None:
        self.projects = ProjectsAPI()
        self.timeout = 30  # a non-sub-client attribute must be ignored


def test_resolves_by_class_name_and_method() -> None:
    client = _FakeClient()
    method = resolve_sdk_method(client, "mammoth.api.projects.ProjectsAPI.list")
    assert method(limit=5) == {"limit": 5}


def test_unknown_class_raises_cli_error() -> None:
    client = _FakeClient()
    with pytest.raises(CliError) as excinfo:
        resolve_sdk_method(client, "mammoth.api.other.OtherAPI.list")
    assert excinfo.value.code == "sdk_symbol_unresolved"


def test_unknown_method_raises_cli_error() -> None:
    client = _FakeClient()
    with pytest.raises(CliError) as excinfo:
        resolve_sdk_method(client, "mammoth.api.projects.ProjectsAPI.absent")
    assert excinfo.value.code == "sdk_symbol_unresolved"


def test_malformed_symbol_raises_cli_error() -> None:
    client = _FakeClient()
    with pytest.raises(CliError) as excinfo:
        resolve_sdk_method(client, "list")
    assert excinfo.value.code == "sdk_symbol_unresolved"


def test_rejects_private_method() -> None:
    client = _FakeClient()
    with pytest.raises(CliError) as excinfo:
        resolve_sdk_method(client, "mammoth.api.projects.ProjectsAPI._secret")
    assert excinfo.value.code == "sdk_symbol_unresolved"
