"""The CLI names itself in the User-Agent, ahead of the SDK it is built on."""

from __future__ import annotations

from mammoth_cli import __version__
from mammoth_cli.context.resolver import ResolvedAuth
from mammoth_cli.runtime import trace
from mammoth_cli.services.sdk_service import SdkMammothService


def test_cli_requests_lead_with_mammoth_cli_user_agent() -> None:
    auth = ResolvedAuth(None, None, 4, "https://app.mammoth.io/api/v2", api_token="mm_unit")
    agent = SdkMammothService(auth)._client.session.headers["User-Agent"]
    assert agent.startswith(f"mammoth-cli/{__version__} mammoth-io/")


def test_each_call_names_the_command_running_now() -> None:
    auth = ResolvedAuth(None, None, 4, "https://app.mammoth.io/api/v2", api_token="mm_unit")
    service = SdkMammothService(auth)

    async def work() -> int:
        return 1

    try:
        # One service serves every line of a ``mammoth run``: each line retags it.
        for command_id in ("project.list", "view.data.get"):
            with trace.begin(command_id) as current:
                assert service._run(work()) == 1
                agent = service._client._default_headers["User-Agent"]
                assert agent.startswith(f"mammoth-cli/{__version__} (cmd={command_id}; ")
                assert f"inv={current.invocation_id}" in agent
                assert " mammoth-io/" in agent
    finally:
        service.close()
