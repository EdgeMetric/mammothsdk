"""``--reveal`` on the commands whose result is a credential the API shows once.

``dashboard embed secret rotate`` returns the new workspace signing secret and
``dashboard embed preview-token create`` a token for the embed simulator. Key
redaction masks both (``secret``, ``token``), which leaves a rotation with no
usable secret. They stay masked by default, so a log or a shared transcript
never holds them; ``--reveal`` prints them, the way ``client-app create`` shows
its token. A secure webhook's ``secret`` (``webhook create``/``get``/``update``) is the
same: masked, it read as a usable value and every post with it failed (mammothsdk#373).
"""

from __future__ import annotations

REVEAL_FLAG = "--reveal"

#: The commands that print their credential when given ``--reveal``.
REVEAL_COMMANDS = frozenset(
    {
        "dashboard.embed.secret.rotate",
        "dashboard.embed.preview-token.create",
        "webhook.create",
        "webhook.get",
        "webhook.update",
    }
)
