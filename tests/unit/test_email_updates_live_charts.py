"""Email updates (collections and dashboards), live charts and oEmbed: the wire each call sends.

Runs against a real loopback HTTP server that records every request.
"""

from __future__ import annotations

from typing import Any

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothValidationError

from ._loopback import RecordingServer
from ._loopback import client as client  # noqa: F401
from ._loopback import server as server  # noqa: F401

UPDATES = {
    "update": {
        "id": 3,
        "enabled": True,
        "trigger": "schedule",
        "frequency": "weekly",
        "weekday": 0,
        "monthday": None,
        "time_of_day": "09:00",
        "timezone": "Europe/Paris",
        "numbers": {"331": ["revenue"]},
    },
    "people": 4,
    "unsubscribed": ["a@example.com"],
    "boards": [],
    "covered_by": [],
}


def _last(server: RecordingServer) -> dict[str, Any]:
    return server.requests[-1]  # type: ignore[return-value]


# ── Collections ──────────────────────────────────────────────


async def test_collection_email_updates_get(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["GET /collections/7/email-updates"] = UPDATES
    assert await client.collections.email_updates(7) == UPDATES
    assert _last(server)["method"] == "GET"
    assert _last(server)["path"] == "/collections/7/email-updates"


async def test_collection_set_email_updates_sends_only_the_fields_given(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["PUT /collections/7/email-updates"] = UPDATES
    await client.collections.set_email_updates(7, True, "Europe/Paris")
    assert _last(server)["body"] == {"enabled": True, "timezone": "Europe/Paris"}


async def test_collection_set_email_updates_sends_every_field(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["PUT /collections/7/email-updates"] = UPDATES
    await client.collections.set_email_updates(
        7,
        False,
        "UTC",
        trigger="schedule",
        frequency="monthly",
        weekday=6,
        monthday=28,
        time_of_day="23:59",
        numbers={"331": ["revenue", "orders"]},
    )
    assert _last(server) == {
        "method": "PUT",
        "path": "/collections/7/email-updates",
        "query": {},
        "body": {
            "enabled": False,
            "timezone": "UTC",
            "trigger": "schedule",
            "frequency": "monthly",
            "weekday": 6,
            "monthday": 28,
            "time_of_day": "23:59",
            "numbers": {"331": ["revenue", "orders"]},
        },
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"enabled": "yes", "timezone": "UTC"},
        {"enabled": True, "timezone": ""},
        {"enabled": True, "timezone": "x" * 65},
        {"enabled": True, "timezone": "UTC", "trigger": "hourly"},
        {"enabled": True, "timezone": "UTC", "frequency": "yearly"},
        {"enabled": True, "timezone": "UTC", "weekday": 7},
        {"enabled": True, "timezone": "UTC", "weekday": -1},
        {"enabled": True, "timezone": "UTC", "monthday": 0},
        {"enabled": True, "timezone": "UTC", "monthday": 29},
        {"enabled": True, "timezone": "UTC", "time_of_day": "9:00"},
        {"enabled": True, "timezone": "UTC", "time_of_day": "24:00"},
        {"enabled": True, "timezone": "UTC", "numbers": {"331": "revenue"}},
        {"enabled": True, "timezone": "UTC", "numbers": ["revenue"]},
    ],
)
async def test_collection_set_email_updates_refuses_bad_input_before_any_request(
    server: RecordingServer, client: MammothClient, kwargs: dict[str, Any]  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError):
        await client.collections.set_email_updates(7, **kwargs)
    assert server.requests == []


async def test_collection_my_email_updates_get_and_set(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["GET /collections/7/email-updates/me"] = {"available": True, "subscribed": True}
    server.answers["PUT /collections/7/email-updates/me"] = {"available": True, "subscribed": False}
    assert await client.collections.my_email_updates(7) == {"available": True, "subscribed": True}
    result = await client.collections.set_my_email_updates(7, False)
    assert result["subscribed"] is False
    assert _last(server) == {
        "method": "PUT",
        "path": "/collections/7/email-updates/me",
        "query": {},
        "body": {"subscribed": False},
    }


async def test_collection_set_my_email_updates_refuses_a_non_bool(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="subscribed"):
        await client.collections.set_my_email_updates(7, "off")  # type: ignore[arg-type]
    assert server.requests == []


async def test_collection_send_test_email_update_posts_to_the_test_route(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /collections/7/email-updates/test"] = {"sent": 1}
    assert await client.collections.send_test_email_update(7) == {"sent": 1}
    assert _last(server)["method"] == "POST"
    assert _last(server)["path"] == "/collections/7/email-updates/test"
    assert _last(server)["body"] is None


@pytest.mark.parametrize(
    "call",
    ["email_updates", "my_email_updates", "send_test_email_update"],
)
async def test_collection_email_calls_refuse_a_bad_collection_id(
    server: RecordingServer, client: MammothClient, call: str  # noqa: F811
) -> None:
    with pytest.raises(MammothValidationError, match="collection_id"):
        await getattr(client.collections, call)(0)
    assert server.requests == []


# ── Dashboards (generated from the pinned spec) ──────────────


async def test_dashboard_email_updates_list_get_set(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["GET /dashboards/email-updates"] = {
        "updates": [
            {"dashboard_id": 331, "enabled": True, "frequency": "weekly", "trigger": "new_data"}
        ]
    }
    server.answers["GET /dashboards/331/email-updates"] = UPDATES
    server.answers["PUT /dashboards/331/email-updates"] = UPDATES

    listed = await client.dashboards.email_updates_list()
    assert listed.updates[0].dashboard_id == 331
    got = await client.dashboards.email_updates_get(331)
    assert got.people == 4
    saved = await client.dashboards.email_updates_set(
        331, {"enabled": True, "timezone": "Europe/Paris", "trigger": "schedule"}
    )
    assert saved.update is not None and saved.update.id == 3
    assert _last(server) == {
        "method": "PUT",
        "path": "/dashboards/331/email-updates",
        "query": {},
        "body": {"enabled": True, "timezone": "Europe/Paris", "trigger": "schedule"},
    }


async def test_dashboard_my_email_updates_and_test_send(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["GET /dashboards/331/email-updates/me"] = {"available": True, "subscribed": True}
    server.answers["PUT /dashboards/331/email-updates/me"] = {
        "available": True,
        "subscribed": False,
    }
    server.answers["POST /dashboards/331/email-updates/test"] = {"sent": 1}
    assert (await client.dashboards.email_updates_me_get(331)).subscribed is True
    off = await client.dashboards.email_updates_me_set(331, {"subscribed": False})
    assert off.subscribed is False
    assert _last(server)["body"] == {"subscribed": False}
    sent = await client.dashboards.email_updates_test(331)
    assert sent.sent == 1
    assert _last(server)["path"] == "/dashboards/331/email-updates/test"


# ── Live charts and oEmbed ───────────────────────────────────

CHART = {
    "dashboard_id": 500,
    "title": "Revenue",
    "token": "tok",
    "state": "live",
    "audience": "workspace",
    "allowed_origins": [],
    "view_id": 88,
    "created_at": "2026-10-14T10:00:00Z",
    "embed_url": "https://app.mammoth.io/embed/tok",
    "share_url": "https://app.mammoth.io/share/tok",
    "oembed": True,
}


async def test_live_chart_list_sends_the_session_id(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["GET /dashboards/v3/live-charts"] = {
        "items": [
            {
                "dashboard_id": 500,
                "message_id": "m1",
                "chart_index": 0,
                "state": "live",
                "audience": "workspace",
            }
        ]
    }
    result = await client.dashboards.live_chart_list("sess-1")
    assert _last(server)["query"] == {"session_id": "sess-1"}
    assert result.items[0].dashboard_id == 500


async def test_live_chart_create_posts_the_params_and_project(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["POST /dashboards/v3/live-charts"] = (202, {"dashboard_id": 500, "job_id": 12})
    spec = {
        "params": {
            "view_id": 88,
            "figure": {"kind": "bar"},
            "title": "Revenue",
            "audience": "workspace",
        }
    }
    created = await client.dashboards.live_chart_create(spec, project_id=25654)
    assert created.dashboard_id == 500 and created.job_id == 12
    assert _last(server) == {
        "method": "POST",
        "path": "/dashboards/v3/live-charts",
        "query": {"project_id": "25654"},
        "body": {
            "params": {
                "view_id": 88,
                "figure": {"kind": "bar"},
                "title": "Revenue",
                "audience": "workspace",
            }
        },
    }


async def test_live_chart_get_audience_usage_and_placement(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["GET /dashboards/v3/live-charts/500"] = CHART
    server.answers["PATCH /dashboards/v3/live-charts/500"] = {**CHART, "audience": "public"}
    server.answers["GET /dashboards/v3/live-charts/500/usage"] = {
        "embeds": [{"origin": "https://blog.example.com", "renders_30d": 9}],
        "dashboards": [],
        "link_views_30d": 2,
    }
    server.answers["POST /dashboards/v3/live-charts/500/placements"] = (204, None)

    assert (await client.dashboards.live_chart_get(500)).state == "live"
    changed = await client.dashboards.live_chart_audience(500, {"params": {"audience": "public"}})
    assert changed.audience == "public"
    assert _last(server)["method"] == "PATCH"
    assert _last(server)["body"] == {"params": {"audience": "public"}}
    usage = await client.dashboards.live_chart_usage(500)
    assert usage.embeds[0].renders_30d == 9 and usage.link_views_30d == 2
    await client.dashboards.live_chart_placement(
        500, {"params": {"dashboard_id": 331, "figure_id": "fig-1"}}
    )
    assert _last(server) == {
        "method": "POST",
        "path": "/dashboards/v3/live-charts/500/placements",
        "query": {},
        "body": {"params": {"dashboard_id": 331, "figure_id": "fig-1"}},
    }


async def test_oembed_sends_only_the_options_given(
    server: RecordingServer, client: MammothClient  # noqa: F811
) -> None:
    server.answers["GET /dashboards/oembed"] = {"type": "rich", "html": "<iframe></iframe>"}
    result = await client.dashboards.oembed(url="https://app.mammoth.io/url/abc", maxwidth="600")
    assert result["type"] == "rich"
    assert _last(server)["query"] == {"url": "https://app.mammoth.io/url/abc", "maxwidth": "600"}
