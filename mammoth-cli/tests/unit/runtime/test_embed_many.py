"""``invoke_many`` batches and the token login's workspace hint."""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.context import resolver
from mammoth_cli.context.resolver import ExplicitLogin, ResolvedAuth
from mammoth_cli.embed import invoke, invoke_many
from mammoth_cli.errors.envelope import EXIT_AUTH, CliError
from mammoth_cli.runtime import embedded
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.testing import FakeMammothService

LIST_PROJECTS = "mammoth.api.projects.ProjectsAPI.list"
CURRENT_WORKSPACE = "mammoth.api.workspace.WorkspaceAPI.current"

#: The workspace each test token belongs to, as the server would answer.
_TOKEN_WORKSPACE = {"jwt-user": 5}


@pytest.fixture
def lookups(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """The tokens the CLI asked the server about; no network here."""
    asked: list[str] = []

    def _resolve(_base_url: str, token: str, _timeout: float | None) -> int:
        asked.append(token)
        return _TOKEN_WORKSPACE[token]

    monkeypatch.setattr(resolver, "resolve_token_workspace", _resolve)
    return asked


@pytest.fixture
def built(monkeypatch: pytest.MonkeyPatch) -> list[FakeMammothService]:
    """Every service the CLI built, in order."""
    services: list[FakeMammothService] = []

    def _build(_auth: ResolvedAuth, **_kwargs: Any) -> FakeMammothService:
        services.append(FakeMammothService())
        return services[-1]

    monkeypatch.setattr(service_factory, "build_service", _build)
    return services


def _login(workspace_id: int | None = None) -> ExplicitLogin:
    return ExplicitLogin(
        api_key=None,
        api_secret=None,
        api_token="jwt-user",
        server_prefix="box",
        workspace_id=workspace_id,
    )


def _denied() -> CliError:
    return CliError(
        code="authorization_required",
        message="denied",
        exit_status=EXIT_AUTH,
        authorization_required=True,
    )


def test_a_workspace_hint_saves_the_lookup(
    lookups: list[str], built: list[FakeMammothService]
) -> None:
    envelope = invoke(["project", "list"], login=_login(workspace_id=5))

    assert envelope["meta"]["workspace_id"] == 5
    assert lookups == []


def test_without_a_hint_the_token_names_its_workspace(
    lookups: list[str], built: list[FakeMammothService]
) -> None:
    envelope = invoke(["project", "list"], login=_login())

    assert envelope["meta"]["workspace_id"] == 5
    assert lookups == ["jwt-user"]


def test_a_non_positive_hint_is_refused(
    lookups: list[str], built: list[FakeMammothService]
) -> None:
    envelope = invoke(["project", "list"], login=_login(workspace_id=0))

    assert envelope["error"]["code"] == "invalid_workspace_id"


def test_a_403_under_a_wrong_hint_is_a_workspace_mismatch(
    lookups: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeMammothService()
    fake.responses[LIST_PROJECTS] = _denied()
    monkeypatch.setattr(service_factory, "build_service", lambda _auth, **_kw: fake)

    envelope = invoke(["project", "list"], login=_login(workspace_id=6))

    assert envelope["error"]["code"] == "workspace_mismatch"
    assert envelope["error"]["details"] == {"workspace_id": 6, "token_workspace_id": 5}
    assert lookups == ["jwt-user"]


def test_a_403_under_a_right_hint_stays_a_refusal(
    lookups: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeMammothService()
    fake.responses[LIST_PROJECTS] = _denied()
    monkeypatch.setattr(service_factory, "build_service", lambda _auth, **_kw: fake)

    envelope = invoke(["project", "list"], login=_login(workspace_id=5))

    assert envelope["error"]["code"] == "authorization_required"


def test_a_403_without_a_hint_asks_nothing_more(
    lookups: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeMammothService()
    fake.responses[LIST_PROJECTS] = _denied()
    monkeypatch.setattr(service_factory, "build_service", lambda _auth, **_kw: fake)

    envelope = invoke(["project", "list"], login=_login())

    assert envelope["error"]["code"] == "authorization_required"
    assert lookups == ["jwt-user"]  # the resolve itself, not a second check


def test_a_batch_shares_one_service_and_closes_it_at_the_end(
    lookups: list[str], built: list[FakeMammothService], capsys: pytest.CaptureFixture[str]
) -> None:
    envelopes = invoke_many(
        [["project", "list"], ["project", "list"], ["project", "list"]],
        login=_login(workspace_id=5),
        project_id=42,
    )

    assert [envelope["meta"]["project_id"] for envelope in envelopes] == [42, 42, 42]
    assert len(built) == 1
    assert built[0].calls.count("close") == 1
    assert capsys.readouterr() == ("", "")
    assert embedded.current() is None


def test_a_failure_stops_the_batch_and_skips_the_rest(
    lookups: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeMammothService()
    monkeypatch.setattr(service_factory, "build_service", lambda _auth, **_kw: fake)

    envelopes = invoke_many(
        [["project", "list"], ["project", "no-such-command"], ["project", "list"], ["view"]],
        login=_login(workspace_id=5),
    )

    assert "meta" in envelopes[0]
    assert envelopes[1]["error"]["code"] in {"usage_error", "unknown_command"}
    for index in (2, 3):
        error = envelopes[index]["error"]
        assert error["code"] == "skipped"
        assert error["details"] == {
            "index": index,
            "reason": "earlier_command_failed",
            "failed_index": 1,
        }
    assert len(envelopes) == 4


def test_without_stop_on_error_every_command_runs(
    lookups: list[str], built: list[FakeMammothService]
) -> None:
    envelopes = invoke_many(
        [["project", "no-such-command"], ["project", "list"]],
        login=_login(workspace_id=5),
        stop_on_error=False,
    )

    assert "error" in envelopes[0]
    assert envelopes[1]["meta"]["workspace_id"] == 5


def test_a_success_with_a_failing_exit_stops_the_batch(
    lookups: list[str], built: list[FakeMammothService], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A write whose read-back says it did not take effect carries ``meta.exit``."""
    import mammoth_cli.embed as embed

    real = embed._invoke_one
    answers = iter([{"meta": {"exit": 4}}, None])

    def _one(argv: list[str], login: ExplicitLogin) -> dict[str, Any]:
        answer = next(answers)
        return answer if answer is not None else real(argv, login)

    monkeypatch.setattr(embed, "_invoke_one", _one)

    envelopes = invoke_many(
        [["project", "list"], ["project", "list"]], login=_login(workspace_id=5)
    )

    assert envelopes[1]["error"]["code"] == "skipped"


def test_an_empty_batch_returns_nothing(built: list[FakeMammothService]) -> None:
    assert invoke_many([], login=_login(workspace_id=5)) == []
    assert built == []


def test_a_batch_reads_the_project_pin_once(
    lookups: list[str], built: list[FakeMammothService]
) -> None:
    """The pin is fixed for a credential; an embedded call has no disk cache for it."""
    invoke_many([["project", "list"]] * 3, login=_login(workspace_id=5))

    asked = [symbol for symbol, _kwargs in built[0].call_log if symbol == CURRENT_WORKSPACE]
    assert len(asked) == 1


def test_a_closed_service_does_not_lend_its_pin_to_a_new_one() -> None:
    """The answer is kept with its service, so a reused ``id`` never matches."""
    from mammoth_cli.runtime.shared import FIXED_ANSWERS, shared_services
    from mammoth_cli.runtime.token_scope import pinned_projects

    first, second = FakeMammothService(), FakeMammothService()
    first.responses[CURRENT_WORKSPACE] = {"projects": [7]}
    second.responses[CURRENT_WORKSPACE] = {"projects": [8]}
    with shared_services():
        assert pinned_projects(first) == (7,)
        fixed = FIXED_ANSWERS.get()
        assert fixed is not None
        fixed[id(second)] = fixed.pop(id(first))  # as if ``second`` took the freed id
        assert pinned_projects(second) == (8,)


def test_reads_kept_ahead_of_a_write_do_not_reach_the_next_command(
    lookups: list[str], built: list[FakeMammothService], monkeypatch: pytest.MonkeyPatch
) -> None:
    import mammoth_cli.embed as embed

    real = embed._invoke_one
    seen: list[bool] = []

    def _one(argv: list[str], login: ExplicitLogin) -> dict[str, Any]:
        envelope = real(argv, login)
        if built:
            seen.append(built[0].memo.lookup("some.Symbol", {})[0])
            built[0].memo.store("some.Symbol", {}, "stale")
        return envelope

    monkeypatch.setattr(embed, "_invoke_one", _one)

    invoke_many([["project", "list"]] * 2, login=_login(workspace_id=5))

    assert seen == [False, False]


def test_every_envelope_carries_its_wall_time(
    lookups: list[str], built: list[FakeMammothService]
) -> None:
    envelopes = invoke_many(
        [["project", "list"], ["project", "no-such-command"], ["project", "list"]],
        login=_login(workspace_id=5),
    )

    assert isinstance(envelopes[0]["meta"]["elapsed_ms"], int)
    assert isinstance(envelopes[1]["error"]["elapsed_ms"], int)
    assert envelopes[2]["error"]["elapsed_ms"] == 0
    assert isinstance(invoke(["project", "list"], login=_login(5))["meta"]["elapsed_ms"], int)
