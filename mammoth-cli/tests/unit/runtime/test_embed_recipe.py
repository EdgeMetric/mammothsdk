"""``recipe run`` embedded: each line is a step of the host's call; the host gets one envelope."""

from __future__ import annotations

import threading
from typing import Any

import pytest

from mammoth_cli import embed
from mammoth_cli.context import resolver
from mammoth_cli.context.resolver import ExplicitLogin, ResolvedAuth
from mammoth_cli.embed import invoke
from mammoth_cli.runtime import embedded
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.testing import FakeMammothService

_STUCK = ["recipe", "run", "stuck-upload", "--input", '{"inputs": {"dataset_id": 7}}']


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch) -> list[ResolvedAuth]:
    """Every login a service was built for; no network."""
    monkeypatch.setattr(resolver, "resolve_token_workspace", lambda *_args: 5)
    logins: list[ResolvedAuth] = []

    def _build(auth: ResolvedAuth, **_kwargs: Any) -> FakeMammothService:
        logins.append(auth)
        return FakeMammothService()

    monkeypatch.setattr(service_factory, "build_service", _build)
    return logins


def _login(token: str = "jwt-user") -> ExplicitLogin:
    return ExplicitLogin(
        api_key=None, api_secret=None, api_token=token, server_prefix="box", workspace_id=5
    )


def test_an_embedded_recipe_returns_one_envelope_with_each_line(
    _offline: list[ResolvedAuth],
) -> None:
    envelope = invoke(_STUCK, login=_login(), project_id=9)
    assert "error" not in envelope, envelope
    data = envelope["data"]
    assert data["recipe"] == "stuck-upload"
    assert [line["cmd"] for line in data["lines_run"]] == [
        "dataset get",
        "dataset file-settings get",
    ]
    assert all(line["exit"] == 0 for line in data["lines_run"])
    assert data["ok"] == 2 and data["failed"] == 0
    # Every line ran as the host's login, none from a profile on disk.
    assert {auth.api_token for auth in _offline} == {"jwt-user"}


def test_each_line_is_a_step_of_the_hosts_call(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[list[str], ExplicitLogin | None]] = []
    real = embed.invoke_step

    def _step(argv: list[str]) -> dict[str, Any]:
        call = embedded.current()
        seen.append((list(argv), call.login if call else None))
        return real(argv)

    monkeypatch.setattr(embed, "invoke_step", _step)
    login = _login()
    invoke(_STUCK, login=login, project_id=9)
    assert [argv[:2] for argv, _ in seen] == [["dataset", "get"], ["dataset", "file-settings"]]
    assert all(step_login is login for _, step_login in seen)
    assert all("--project=9" in argv for argv, _ in seen)


def test_concurrent_embedded_recipes_keep_their_own_lines(
    _offline: list[ResolvedAuth],
) -> None:
    results: dict[str, dict[str, Any]] = {}

    def _run(token: str) -> None:
        results[token] = invoke(_STUCK, login=_login(token), project_id=9)

    threads = [threading.Thread(target=_run, args=(f"jwt-{n}",)) for n in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    for envelope in results.values():
        assert "error" not in envelope, envelope
        assert len(envelope["data"]["lines_run"]) == 2


def test_a_recipe_that_reads_a_local_file_is_refused_before_any_line_runs() -> None:
    envelope = invoke(
        ["recipe", "run", "append-rows", "--input"]
        + ['{"inputs": {"dataset_id": 7, "file": "/etc/passwd"}}', "--yes"],
        login=_login(),
        project_id=9,
    )
    assert envelope["error"]["code"] == "not_available_embedded"
