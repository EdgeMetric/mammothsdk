"""The CLI names itself in the User-Agent, ahead of the SDK it is built on."""

from __future__ import annotations

from mammoth_cli import __version__
from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.services.sdk_service import SdkMammothService


def test_cli_requests_lead_with_mammoth_cli_user_agent() -> None:
    auth = ResolvedAuth(None, None, 4, "https://app.mammoth.io/api/v2", api_token="mm_unit")
    agent = SdkMammothService(auth)._client.session.headers["User-Agent"]
    assert agent.startswith(f"mammoth-cli/{__version__} mammoth-io/")
