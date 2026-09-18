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
