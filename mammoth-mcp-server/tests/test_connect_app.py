"""The button drawn in the chat to connect a source, instead of a bare link.

A client with MCP Apps draws the page `connect_source` points at under the
call: one button that opens the connector in Mammoth. A client without MCP
Apps shows `mammoth_url`, which `test_tools_sources.py` covers.
"""

from mcp.server.apps import APP_MIME_TYPE

from .test_upload_app import UI, find_tool_meta, read_app


class TestConnectApp:
    def app_uri(self) -> str:
        return find_tool_meta("connect_source")[UI]["resourceUri"]

    def test_connect_source_points_at_a_page_the_server_serves_as_an_app(self) -> None:
        page, mime_type, _ = read_app(self.app_uri())

        assert mime_type == APP_MIME_TYPE
        assert "<button" in page

    def test_the_button_reads_the_link_from_the_tool_result(self) -> None:
        page, _, _ = read_app(self.app_uri())

        assert "ui/initialize" in page
        assert "ui/notifications/tool-result" in page
        assert '"mammoth_url"' in page

    def test_the_host_opens_the_link_and_the_link_shows_when_it_cannot(self) -> None:
        # A sandboxed frame may not open a window itself: it asks the host.
        page, _, _ = read_app(self.app_uri())

        assert "ui/open-link" in page
        assert "<a " in page

    def test_the_page_watches_for_the_connection_and_tells_the_chat(self) -> None:
        # The card keeps calling `find_new_connection` for the whole watch, and puts a
        # turn in the chat when the connection is made, so nobody types "done".
        page, _, _ = read_app(self.app_uri())

        assert '"find_new_connection"' in page
        assert "ui/message" in page

    def test_the_page_reaches_nothing(self) -> None:
        # It only hands the host a link, so its sandbox needs no domain.
        _, _, meta = read_app(self.app_uri())

        assert not (meta.get(UI, {}).get("csp") or {}).get("connectDomains")
