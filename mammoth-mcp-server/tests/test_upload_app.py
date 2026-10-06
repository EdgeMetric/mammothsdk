"""The uploader drawn inside the chat, instead of behind a link.

A client that speaks MCP Apps renders the `ui://` page a tool points at in a
sandboxed frame under the tool call. These tests pin what that needs from the
server: `request_upload` names the page, the page is served as an app, its
sandbox may reach the upload route, and the page speaks the host's protocol —
it reads the link from the tool result, and tells the chat when it is done.

A client without MCP Apps ignores all of it and shows `upload_url`, which
`test_upload_handoff.py` covers.
"""

from urllib.parse import urlparse

from mcp.server.apps import APP_MIME_TYPE

from mammoth_mcp_server.config import MCP_UPLOAD_URL
from mammoth_mcp_server.server import mcp_server, register_tools

from .helpers import run

UI = "ui"


def find_tool_meta(name: str) -> dict:
    register_tools()
    tools = {tool.name: tool for tool in run(mcp_server.list_tools())}
    meta = tools[name].meta
    assert meta is not None
    return meta


def read_app(uri: str) -> tuple[str, str | None, dict]:
    [contents] = list(run(mcp_server.read_resource(uri)))
    assert isinstance(contents.content, str)
    return contents.content, contents.mime_type, contents.meta or {}


class TestUploadApp:
    def app_uri(self) -> str:
        return find_tool_meta("request_upload")[UI]["resourceUri"]

    def test_request_upload_points_at_a_page_the_server_serves_as_an_app(
        self,
    ) -> None:
        page, mime_type, _ = read_app(self.app_uri())

        assert mime_type == APP_MIME_TYPE
        assert 'type="file"' in page

    def test_the_sandbox_may_reach_the_upload_route(self) -> None:
        # The host's default policy forbids every fetch; without this the drop
        # zone renders and every upload from it fails.
        _, _, meta = read_app(self.app_uri())
        upload = urlparse(MCP_UPLOAD_URL)

        assert f"{upload.scheme}://{upload.netloc}" in (meta[UI]["csp"]["connectDomains"])

    def test_the_page_reads_the_link_from_the_tool_result(self) -> None:
        page, _, _ = read_app(self.app_uri())

        assert "ui/initialize" in page
        assert "ui/notifications/tool-result" in page
        assert "structuredContent" in page

    def test_the_page_tells_the_chat_once_the_files_are_in(self) -> None:
        # `ui/message` puts a user turn in the chat, so the model carries on
        # without the user typing; `check_upload` is how the page knows.
        page, _, _ = read_app(self.app_uri())

        assert '"check_upload"' in page
        assert "ui/message" in page
        assert "ui/update-model-context" in page

    def test_the_chat_is_told_when_the_upload_waits_on_a_choice(self) -> None:
        # The turn the page posts is what the model reads next: if it does not
        # say a choice is waiting, the upload looks finished.
        page, _, _ = read_app(self.app_uri())

        assert "do not choose for me" in page
