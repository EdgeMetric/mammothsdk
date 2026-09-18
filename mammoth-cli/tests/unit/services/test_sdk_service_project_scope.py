"""Project-scope preflight tests for release view seams."""

from __future__ import annotations

import pytest

from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.sdk_service import SdkMammothService

AUTH = ResolvedAuth(
    api_key="key",
    api_secret="secret",
    workspace_id=4,
    base_url="https://unused.invalid/api/v2",
)


@pytest.fixture
def service() -> SdkMammothService:
    instance = SdkMammothService(AUTH)
    try:
        yield instance
    finally:
        instance.close()


def test_transform_call_view_requires_project_before_resolution(service: SdkMammothService) -> None:
    with pytest.raises(CliError) as excinfo:
        service.call_view(285, "math", dataset_id=365, expression="column_2 * column_3")
    assert excinfo.value.code == "project_required"
    assert excinfo.value.exit_status == 2


@pytest.mark.parametrize(
    "symbol, kwargs",
    [
        ("mammoth.api.pipeline.PipelineAPI.items_all", {"dataview_id": 285, "dataset_id": 365}),
        ("mammoth.client.ViewsResource.delete", {"view_id": 285, "dataset_id": 365}),
    ],
)
def test_project_scoped_view_calls_require_project_before_transport(
    service: SdkMammothService, symbol: str, kwargs: dict[str, int]
) -> None:
    with pytest.raises(CliError) as excinfo:
        service.call(symbol, **kwargs)
    assert excinfo.value.code == "project_required"
    assert excinfo.value.exit_status == 2


def test_parent_discovery_miss_is_a_named_not_found_error(
    service: SdkMammothService, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The SDK reports a discovery miss as a bare ValueError; before this
    # mapping the CLI flattened it into "operation failed unexpectedly".
    service._client.set_project_id(4301)

    def _miss(view_id: int) -> object:
        raise ValueError(f"Dataview {view_id} not found in any dataset in project 4301")

    monkeypatch.setattr(service._client, "get_view", _miss)
    with pytest.raises(CliError) as excinfo:
        service.call_view(308772, "get_data")
    assert excinfo.value.code == "resource_not_found"
    assert excinfo.value.exit_status == 5
    assert excinfo.value.details["reason"].endswith("project 4301")
    assert excinfo.value.recovery_commands[0] == (
        "mammoth dataset list --project 4301 --output json --no-input"
    )


def test_parent_discovery_miss_on_the_generic_call_path_is_not_found_too(
    service: SdkMammothService, monkeypatch: pytest.MonkeyPatch
) -> None:
    # ``view get`` / ``view task list`` dispatch through ``call`` with the
    # ViewsResource symbol; a deleted view must read as not_found there as
    # well, not as a generic api_error ValueError.
    service._client.set_project_id(4301)

    def _miss(view_id: int, dataset_id: int | None = None) -> object:
        raise ValueError(f"Dataview {view_id} not found in any dataset in project 4301")

    monkeypatch.setattr(service._client.views, "get", _miss)
    with pytest.raises(CliError) as excinfo:
        service.call("mammoth.client.ViewsResource.get", view_id=79)
    assert excinfo.value.code == "resource_not_found"
    assert excinfo.value.exit_status == 5
    assert excinfo.value.details == {
        "view_id": 79,
        "project_id": 4301,
        "reason": "Dataview 79 not found in any dataset in project 4301",
    }


@pytest.mark.parametrize(
    ("method", "view_kwarg", "parent_kwarg"),
    [
        ("join", "foreign_view", "foreign_dataset_id"),
        ("lookup", "lookup_view_id", "lookup_dataset_id"),
    ],
)
def test_foreign_view_without_parent_is_refused_before_discovery(
    service: SdkMammothService,
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    view_kwarg: str,
    parent_kwarg: str,
) -> None:
    service._client.set_project_id(4300)
    probed: list[int] = []

    class _View:
        columns: dict[str, str] = {}

        def join(self, **kwargs: object) -> None:
            raise AssertionError("must not dispatch")

        def lookup(self, **kwargs: object) -> None:
            raise AssertionError("must not dispatch")

    monkeypatch.setattr(service._client.views, "get", lambda view_id, dataset_id=None: _View())
    monkeypatch.setattr(
        service._client, "get_view", lambda view_id: probed.append(view_id) or _View()
    )
    with pytest.raises(CliError) as excinfo:
        service.call_view(308758, method, dataset_id=1, **{view_kwarg: 308756})
    assert excinfo.value.code == "missing_argument"
    assert excinfo.value.details == {view_kwarg: 308756, "missing_field": parent_kwarg}
    assert probed == []
