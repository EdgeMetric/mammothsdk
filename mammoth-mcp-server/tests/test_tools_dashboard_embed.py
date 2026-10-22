"""Putting a dashboard on another site: the code to paste, and who may frame it.

`get_dashboard` reads the embed and `edit_dashboard` changes it: no tool of its own.
"""

from typing import Any

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from .helpers import WORKSPACE, FakeApi, a_fake_api, as_caller, call_tool

DASHBOARD_ID = 42
DASHBOARD = f"/dashboards/{DASHBOARD_ID}"
CONFIG = f"{DASHBOARD}/embed/config"
BOARD = {
    "id": DASHBOARD_ID,
    "title": "Sales",
    "url": "abc123",
    "engine": "v3",
    "was_published": True,
}
EMBED_URL = "https://app.example.com/api/v2/dashboards/embed/abc123"

ON_KEY: dict[str, Any] = {
    "mode": "key",
    "tier": "key",
    "allow_any_origin": True,
    "allowed_origins": [],
    "appearance": {},
    "snippet": {},
    "embed_url": EMBED_URL,
    "sdk_url": "https://app.example.com/embed-assets/mammoth-embed.js",
    "published": True,
    "public": False,
    "access_key": "ek_live_123",
    "has_signing_secret": True,
    "token_ttl": 300,
    "rls_enabled": False,
}
SIGNED = {**ON_KEY, "mode": "signed", "tier": "signed"}
PUBLIC = {**ON_KEY, "mode": "public", "public": True, "access_key": None}


def a_board(api: FakeApi, config: dict[str, Any] = ON_KEY) -> None:
    api.answer("GET", DASHBOARD, BOARD)
    api.answer("GET", CONFIG, config)
    api.answer("PUT", CONFIG, config)


def get_embed() -> Any:
    board = call_tool(
        "get_dashboard",
        workspace_id=WORKSPACE,
        dashboard_id=DASHBOARD_ID,
        include_values=False,
        include_embed=True,
    )
    return board["embed"]


def set_embed(**arguments: object) -> Any:
    board = call_tool(
        "edit_dashboard", workspace_id=WORKSPACE, dashboard_id=DASHBOARD_ID, **arguments
    )
    return board["embed"]


class TestTheCodeToPaste:
    def test_a_board_on_its_key_carries_the_key(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api)
            embed = get_embed()

        assert f'src="{EMBED_URL}?key=ek_live_123"' in embed["embed_code"]
        assert embed["key"] == "ek_live_123"
        assert "allowed_sites" in embed["next_step"]

    def test_a_signed_board_leaves_the_token_to_the_host(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api, SIGNED)
            embed = get_embed()

        assert f'src="{EMBED_URL}?token=TOKEN"' in embed["embed_code"]
        assert embed["key"] is None
        assert "Replace TOKEN" in embed["next_step"]
        assert "no signing secret" not in embed["next_step"]

    def test_a_signed_board_in_a_workspace_with_no_secret_shows_nowhere(self) -> None:
        # Mammoth saves "signed" without a secret, and then no host can sign a token.
        with a_fake_api() as api, as_caller():
            a_board(api, {**SIGNED, "has_signing_secret": False})
            embed = get_embed()

        assert "no signing secret" in embed["next_step"]

    def test_a_public_board_needs_nothing_in_its_link(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api, PUBLIC)
            embed = get_embed()

        assert f'src="{EMBED_URL}"' in embed["embed_code"]
        assert "link is public" in embed["next_step"]

    def test_the_saved_height_is_kept(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api, {**ON_KEY, "snippet": {"height": 900}})
            embed = get_embed()

        assert 'height="900"' in embed["embed_code"]

    def test_a_board_with_no_height_saved_gets_the_web_apps_height(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api)
            embed = get_embed()

        assert 'height="640"' in embed["embed_code"]

    def test_an_unpublished_board_says_to_publish_it_first(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api, {**ON_KEY, "published": False})
            embed = get_embed()

        assert "publish_dashboard" in embed["next_step"]

    def test_who_may_frame_it_is_reported(self) -> None:
        listed = {**ON_KEY, "allow_any_origin": False, "allowed_origins": ["https://acme.com"]}
        with a_fake_api() as api, as_caller():
            a_board(api, listed)
            embed = get_embed()

        assert embed["any_site"] is False
        assert embed["allowed_sites"] == ["https://acme.com"]
        # Telling a model to limit the sites again would read as if they were open.
        assert "edit_dashboard" not in embed["next_step"]
        assert "Only the allowed sites" in embed["next_step"]

    def test_nothing_about_the_signing_secret_but_whether_there_is_one(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api, {**ON_KEY, "signing_secret": "never-shown"})
            embed = get_embed()

        assert "never-shown" not in str(embed)
        assert embed["has_signing_secret"] is True


class TestWhoMayFrameIt:
    def test_listed_sites_alone_may_frame_it(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api)
            set_embed(allowed_sites=["https://acme.com"])

        [sent] = api.sent("PUT", CONFIG)
        assert api.body(sent) == {
            "params": {"allow_any_origin": False, "allowed_origins": ["https://acme.com"]}
        }

    def test_any_site_may_frame_it_again(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api)
            set_embed(any_site=True)

        [sent] = api.sent("PUT", CONFIG)
        assert api.body(sent) == {"params": {"allow_any_origin": True}}

    def test_the_mode_alone_changes(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api)
            embed = set_embed(embed_mode="signed")

        [sent] = api.sent("PUT", CONFIG)
        assert api.body(sent) == {"params": {"mode": "signed"}}
        assert "embed_code" in embed

    def test_any_site_and_a_list_of_sites_cannot_both_be_asked_for(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api)
            with pytest.raises(ToolError, match="either"):
                set_embed(any_site=True, allowed_sites=["https://acme.com"])

        assert not api.sent("PUT", CONFIG)

    def test_an_unknown_mode_names_the_modes(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api)
            with pytest.raises(ToolError, match="signed"):
                set_embed(embed_mode="open")

        assert not api.sent("PUT", CONFIG)

    def test_a_call_that_changes_nothing_is_refused(self) -> None:
        with a_fake_api() as api, as_caller():
            a_board(api)
            with pytest.raises(ToolError, match="Say what to change"):
                set_embed()

        assert not api.requests


def test_the_embed_is_read_only_when_asked_for() -> None:
    # The config read makes a board its first key, so a plain read leaves it alone.
    with a_fake_api() as api, as_caller():
        a_board(api)
        board = call_tool(
            "get_dashboard", workspace_id=WORKSPACE, dashboard_id=DASHBOARD_ID, include_values=False
        )

    assert "embed" not in board
    assert not api.sent("GET", CONFIG)


def test_an_embed_change_alone_takes_effect_at_once() -> None:
    # Embed settings are not part of the draft, so publishing again is not needed.
    listed = {**ON_KEY, "allow_any_origin": False, "allowed_origins": ["https://acme.com"]}
    with a_fake_api() as api, as_caller():
        a_board(api, listed)
        board = call_tool(
            "edit_dashboard",
            workspace_id=WORKSPACE,
            dashboard_id=DASHBOARD_ID,
            allowed_sites=["https://acme.com"],
        )

    assert "next_step" not in board
    assert "Only the allowed sites" in board["embed"]["next_step"]
