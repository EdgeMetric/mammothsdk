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
