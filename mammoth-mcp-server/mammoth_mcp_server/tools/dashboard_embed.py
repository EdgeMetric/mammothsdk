"""Put a dashboard on another site: the code to paste, and which sites may show it.

No tool of its own: `get_dashboard` reads a board's embed and `edit_dashboard`
changes it, so a model looks for both where it looks for the dashboard.

A published dashboard embeds in one of three ways:
- "public": its share link is public, so the embed needs nothing more.
- "key": the embed code carries the board's embed key. The key is in the
  host page's HTML, so anyone who reads the page has it: the sites the board
  allows are what limit where it shows.
- "signed": the host's own server signs a token for each viewer with the
  workspace's signing secret. The secret is set up in the web app, and no
  tool here reads or changes it.
"""

from typing import Literal

from mammoth.api.dashboards import DashboardsAPI
from mammoth.models.dashboards import EmbedConfigResponse
from mcp.server.mcpserver.exceptions import ToolError

from ..consts import EmbedFields
from ..sdk import JsonValue, read_sdk_errors

type EmbedMode = Literal["key", "signed"]

BOTH_SITE_CHOICES = "Name either any_site=true or a list of allowed_sites, not both."
NOT_PUBLISHED = (
    "The dashboard is not published, so the embed shows nothing. Ask the user,"
    " then call publish_dashboard."
)
PUBLIC_NOTE = "The dashboard's link is public: anyone on a page with this code sees its data."
KEY_NOTE = "The code carries the dashboard's embed key, and anyone who reads the page has it."
ANY_SITE_NOTE = (
    "Any site may show it: to limit where it shows, call edit_dashboard with allowed_sites."
)
LISTED_SITES_NOTE = "Only the allowed sites may show it."
SIGNED_NOTE = (
    "Replace TOKEN with a token the user's own server signs for each viewer. Setting"
    " that up is in the web app."
)
NO_SECRET_NOTE = (
    "The workspace has no signing secret yet, so no token can be signed and the"
    " embed shows nothing. The user sets one up in the web app."
)
MODE_NOTES = {EmbedFields.KEY_MODE: KEY_NOTE}
IFRAME = """<iframe
  src="{src}"
  width="100%" height="{height}"
  frameborder="0" loading="lazy"
  allow="clipboard-write; fullscreen"
  title="Mammoth dashboard">
</iframe>"""


async def read_embed(dashboards: DashboardsAPI, dashboard_id: int) -> dict[str, JsonValue]:
    """A board's embed: the code to paste, which sites may show it, and what to tell the user.

    Mammoth makes a board its embed key the first time its embed is read.
    """
    return describe_embed(await read_sdk_errors(dashboards.embed_config_get(dashboard_id)))


async def change_embed(
    dashboards: DashboardsAPI,
    dashboard_id: int,
    mode: EmbedMode | None,
    any_site: bool | None,
    allowed_sites: list[str] | None,
) -> dict[str, JsonValue]:
    """Save the embed settings named, and return the embed afterwards."""
    # A list of sites is what limits framing: the route reads it only when any site may not.
    any_origin = False if allowed_sites is not None else any_site
    config = await read_sdk_errors(
        dashboards.embed_config_set(
            dashboard_id, mode=mode, allow_any_origin=any_origin, allowed_origins=allowed_sites
        )
    )
    return describe_embed(config)


def check_embed_change(any_site: bool | None, allowed_sites: list[str] | None) -> None:
    """Refuse both any site and a list of sites.

    Raises:
        ToolError: If both are named.
    """
    if any_site and allowed_sites is not None:
        raise ToolError(BOTH_SITE_CHOICES)


def describe_embed(config: EmbedConfigResponse) -> dict[str, JsonValue]:
    """What a model needs of a board's embed settings, and the code to paste."""
    return {
        EmbedFields.MODE: config.mode,
        EmbedFields.EMBED_CODE: embed_code(config),
        EmbedFields.KEY: config.access_key if config.mode == EmbedFields.KEY_MODE else None,
        EmbedFields.ANY_SITE: config.allow_any_origin,
        EmbedFields.ALLOWED_SITES: list[JsonValue](config.allowed_origins),
        EmbedFields.PUBLISHED: config.published,
        EmbedFields.PUBLIC: config.public,
        EmbedFields.HAS_SIGNING_SECRET: config.has_signing_secret,
        EmbedFields.ROW_LEVEL_SECURITY: config.rls_enabled,
        EmbedFields.NEXT_STEP: " ".join(embed_notes(config)),
    }


def embed_notes(config: EmbedConfigResponse) -> list[str]:
    """What to tell the user: what stops the embed showing, then who can see it."""
    notes = [] if config.published else [NOT_PUBLISHED]
    if config.mode == EmbedFields.SIGNED_MODE:
        return [*notes, SIGNED_NOTE, *([] if config.has_signing_secret else [NO_SECRET_NOTE])]
    sites = ANY_SITE_NOTE if config.allow_any_origin else LISTED_SITES_NOTE
    return [*notes, MODE_NOTES.get(config.mode, PUBLIC_NOTE), sites]


def embed_code(config: EmbedConfigResponse) -> str:
    """The iframe the web app gives for the board, carrying its key or a token's place."""
    credential = {
        EmbedFields.KEY_MODE: f"key={config.access_key}" if config.access_key else "",
        EmbedFields.SIGNED_MODE: f"token={EmbedFields.TOKEN_PLACEHOLDER}",
    }.get(config.mode, "")
    src = f"{config.embed_url}?{credential}" if credential else config.embed_url
    return IFRAME.format(src=src, height=frame_height(config.snippet.get(EmbedFields.HEIGHT)))


def frame_height(saved: object) -> int:
    """The frame height the board saved, or the web app's when it saved none."""
    return saved if isinstance(saved, int) else EmbedFields.DEFAULT_HEIGHT
