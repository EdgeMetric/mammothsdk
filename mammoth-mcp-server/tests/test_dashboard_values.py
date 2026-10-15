"""The numbers `get_dashboard` reports: what each card and chart shows, as Mammoth worked it out.

A model asked about a dashboard answers from what the board shows. Without
these numbers it adds up the view's rows itself, and gets them wrong.
"""

from typing import Any

from .helpers import WORKSPACE, FakeApi, a_fake_api, as_caller, call_tool

BOARD = 720
BOARD_PATH = f"/dashboards/{BOARD}"
DESCRIPTOR_DATA = f"{BOARD_PATH}/data"
JOB = 31
CURRENT_BOARD = {"id": BOARD, "title": "Q1 2026 Sales Revenue", "engine": "v3", "url": "abc123"}
PUBLISHED_BOARD = {**CURRENT_BOARD, "was_published": True}
PUBLISHED_PATH = "/dashboards/url/abc123"
PERIOD = {"origin": "period", "label": "Q1 2026"}
CANVAS = {
    "canvas": {
        "focus": {"kpis": [{"label": "Total Revenue"}]},
        "added": [{"id": "t1", "title": "Revenue by Site", "dim": "Site", "measure": "Revenue"}],
    },
    "meta": {
        "sequence": 4,
        "figures": {
            "p1:kpi:0": {"descriptors": {"value": "d1"}},
            "p1:add:t1": {"descriptors": {"main": "d2"}},
            # A filter control carries no number, so it is not reported.
            "p1:filter:0": {"descriptors": {"options": "d3"}},
        },
        "receipts": {
            "p1:kpi:0": {"series": {"value": {"filters": [PERIOD]}}},
            "p1:add:t1": {
                "series": {
                    "main": {
                        "filters": [
                            PERIOD,
                            {"term": {"field": "Channel", "op": "eq", "value": "Online"}},
                        ]
                    }
                }
            },
        },
    },
}
RESULTS = {
    "d1": {"status": "success", "value": 10998.05},
    "d2": {
        "status": "success",
        "data": [{"Site": f"Site {n}", "Revenue": n} for n in range(12)],
    },
}


def a_board_that_evaluates(api: FakeApi, results: dict[str, Any] = RESULTS) -> None:
    api.answer("GET", BOARD_PATH, CURRENT_BOARD)
    api.answer("GET", f"{BOARD_PATH}/canvas", CANVAS)
    api.answer("POST", DESCRIPTOR_DATA, {"job_id": JOB})
    api.answer(
        "GET",
        f"/jobs/{JOB}",
        {"job": {"id": JOB, "status": "success", "response": {"results": results}}},
    )


def get_dashboard(**arguments: Any) -> dict[str, Any]:
    return dict(call_tool("get_dashboard", workspace_id=WORKSPACE, dashboard_id=BOARD, **arguments))


class TestTheNumbersOnABoard:
    def test_a_kpi_card_reports_its_number_and_the_period_it_covers(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board_that_evaluates(api)
            board = get_dashboard()

        assert board["values"][0] == {
            "figure": "p1:kpi:0",
            "kind": "kpi",
            "label": "Total Revenue",
            "period": "Q1 2026",
            "value": 10998.05,
        }

    def test_a_chart_reports_its_first_rows_and_how_many_there_are(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board_that_evaluates(api)
            chart = get_dashboard()["values"][1]

        assert chart["label"] == "Revenue by Site"
        assert chart["filters"] == ["Channel = Online"]
        assert len(chart["series"]["main"]["rows"]) == 10
        assert chart["series"]["main"]["row_count"] == 12

    def test_every_number_comes_from_one_request_for_the_cards_and_charts_only(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board_that_evaluates(api)
            get_dashboard()

        (sent,) = api.sent("POST", DESCRIPTOR_DATA)
        assert api.body(sent) == {"params": {"descriptor_ids": ["d1", "d2"]}}

    def test_a_card_that_fails_to_evaluate_says_why_and_the_others_still_report(self) -> None:
        failed = {**RESULTS, "d1": {"status": "error", "error": "column Revenue is gone"}}
        with a_fake_api() as api, as_caller():
            a_board_that_evaluates(api, failed)
            values = get_dashboard()["values"]

        assert values[0]["error"] == "column Revenue is gone"
        assert values[1]["series"]["main"]["row_count"] == 12

    def test_an_unpublished_board_reports_its_draft_and_says_so(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board_that_evaluates(api)
            board = get_dashboard()

        assert board["values_from"] == "draft"


class TestAPublishedBoard:
    """Its share link opens the published version, so the numbers are that version's."""

    def test_the_numbers_are_the_published_versions_not_the_drafts(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", BOARD_PATH, PUBLISHED_BOARD)
            api.answer("GET", PUBLISHED_PATH + "/canvas", CANVAS)
            api.answer("POST", PUBLISHED_PATH + "/data", {"job_id": JOB})
            api.answer(
                "GET",
                f"/jobs/{JOB}",
                {"job": {"id": JOB, "status": "success", "response": {"results": RESULTS}}},
            )
            board = get_dashboard()

        assert board["values_from"] == "published"
        assert board["values"][0]["value"] == 10998.05
        assert not api.sent("GET", f"{BOARD_PATH}/canvas")
        assert not api.sent("POST", DESCRIPTOR_DATA)


class TestReadingWithoutTheNumbers:
    def test_a_read_that_does_not_want_them_starts_no_job(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", BOARD_PATH, CURRENT_BOARD)
            board = get_dashboard(include_values=False)

        assert board["title"] == "Q1 2026 Sales Revenue"
        assert "values" not in board
        assert "values_unavailable" not in board
        assert not api.sent("GET", f"{BOARD_PATH}/canvas")
        assert not api.sent("POST", DESCRIPTOR_DATA)


class TestABoardWithoutNumbers:
    """The read never fails for want of numbers: the dashboard is still worth reading."""

    def test_a_board_on_the_older_engine_says_it_has_none(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", BOARD_PATH, {**CURRENT_BOARD, "engine": "v2"})
            board = get_dashboard()

        assert board["title"] == "Q1 2026 Sales Revenue"
        assert "values" not in board
        assert "older" in board["values_unavailable"]
        assert not api.sent("GET", f"{BOARD_PATH}/canvas")

    def test_a_refused_evaluation_is_reported_and_the_dashboard_still_comes_back(self) -> None:
        with a_fake_api() as api, as_caller():
            api.answer("GET", BOARD_PATH, CURRENT_BOARD)
            api.answer("GET", f"{BOARD_PATH}/canvas", CANVAS)
            api.answer("POST", DESCRIPTOR_DATA, {"message": "Not allowed"}, status=403)
            board = get_dashboard()

        assert board["share_url"].endswith("/#/dashboard-v3/abc123")
        assert "Not allowed" in board["values_unavailable"]

    def test_a_board_with_no_cards_or_charts_yet_says_so(self) -> None:
        empty = {"canvas": {}, "meta": {"sequence": 1, "figures": {}}}
        with a_fake_api() as api, as_caller():
            api.answer("GET", BOARD_PATH, CURRENT_BOARD)
            api.answer("GET", f"{BOARD_PATH}/canvas", empty)
            board = get_dashboard()

        assert board["values_unavailable"] == "The dashboard has no cards or charts yet."
        assert not api.sent("POST", DESCRIPTOR_DATA)
