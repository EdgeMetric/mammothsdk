"""What the dashboard tools make of an answer, without a dashboard."""

from mammoth_mcp_server.tools.dashboards import (
    dashboard_links,
    describe_unfinished_build,
    drop_the_rendered_page,
)


class TestTheLinksAUserOpens:
    """Which link is which, without a dashboard: the engine decides both routes.

    A v3 board on the v2 viewer route draws an empty page, and the editor route
    on the viewer host bounces back to the viewer, so a link built on the wrong
    half of either pair looks like a working link and is not.
    """

    def test_a_current_dashboard_is_read_and_edited_on_the_v3_routes(self) -> None:
        links = dashboard_links({"id": 7, "url": "abc123", "engine": "v3"}, 3)

        assert links["share_url"].endswith("/#/dashboard-v3/abc123")
        assert links["editor_url"].endswith("/#/workspaces/3/publish/7")

    def test_an_older_dashboard_keeps_the_routes_its_engine_draws(self) -> None:
        links = dashboard_links({"id": 7, "url": "abc123", "engine": "v2"}, 3)

        assert links["share_url"].endswith("/#/dashboard/abc123")
        assert links["editor_url"].endswith("/#/workspaces/3/dashboard/7")

    def test_a_dashboard_naming_no_engine_is_read_as_the_older_one(self) -> None:
        # A null engine is a v2 row: v3 names itself.
        links = dashboard_links({"id": 7, "url": "abc123"}, 3)

        assert links["share_url"].endswith("/#/dashboard/abc123")

    def test_a_dashboard_with_no_link_of_its_own_is_given_none(self) -> None:
        # A build still going has no url yet, and half a link is worse than none.
        assert dashboard_links({"id": 7, "engine": "v3"}, 3)["share_url"] is None


class TestReadingADashboardBuiltOnTheOlderEngine:
    """The older engine answers with a whole rendered page; a model cannot use it.

    No dashboard the tools create carries those fields, so the payload is built
    here rather than fetched — otherwise the assertion would hold whether or not
    anything was dropped.
    """

    def test_the_rendered_page_and_its_messages_are_dropped(self) -> None:
        kept = drop_the_rendered_page(
            {
                "id": 7,
                "title": "An older dashboard",
                "html": "<html>" + "x" * 500_000 + "</html>",
                "messages": [{"role": "user", "content": "build me a dashboard"}],
                "url": "abc123",
            }
        )

        assert kept == {"id": 7, "title": "An older dashboard", "url": "abc123"}

    def test_a_dashboard_without_them_is_left_alone(self) -> None:
        current = {"id": 9, "title": "A current dashboard", "sources": [3]}

        assert drop_the_rendered_page(current) == current


class TestABuildStillGoing:
    """What a model is told when the wait runs out before the build is done."""

    def test_the_dashboard_being_built_is_named(self) -> None:
        job = {"id": 11, "status": "processing", "response": {"id": 42}}

        assert describe_unfinished_build(job) == {"id": 42, "status": "building"}

    def test_a_build_that_has_made_no_dashboard_yet_says_so(self) -> None:
        job = {"id": 11, "status": "processing", "response": None}

        assert describe_unfinished_build(job) == {"id": None, "status": "building"}
