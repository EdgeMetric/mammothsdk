"""The form drawn under `preview_query`, so the user settles everything in one go.

Choosing what to pull, how often and what a refresh does would otherwise be
three questions in the chat. The form shows the first rows with the query, the
name, the schedule and the refresh already filled in, and one button makes the
dataset.
"""

from mcp.server.apps import APP_MIME_TYPE

from .test_upload_app import UI, find_tool_meta, read_app


class TestDatasetApp:
    def app_uri(self) -> str:
        return find_tool_meta("preview_query")[UI]["resourceUri"]

    def test_preview_query_points_at_a_page_the_server_serves_as_an_app(self) -> None:
        page, mime_type, _ = read_app(self.app_uri())

        assert mime_type == APP_MIME_TYPE
        assert "<textarea" in page
        assert "<select" in page

    def test_once_and_replace_are_what_the_form_starts_on(self) -> None:
        page, _, _ = read_app(self.app_uri())

        assert 'value="once" selected' in page
        assert 'value="replace" selected' in page

    def test_the_button_makes_the_dataset_and_tells_the_chat(self) -> None:
        page, _, _ = read_app(self.app_uri())

        assert "ui/notifications/tool-result" in page
        assert '"add_dataset_from_connection"' in page
        assert "ui/message" in page

    def test_the_page_reaches_nothing(self) -> None:
        _, _, meta = read_app(self.app_uri())

        assert not (meta.get(UI, {}).get("csp") or {}).get("connectDomains")
