"""``--reveal`` on the commands whose result is a credential the API shows once.

``dashboard embed secret rotate`` returns the new workspace signing secret and
``dashboard embed preview-token create`` a token for the embed simulator. Key
redaction masks both (``secret``, ``token``), which leaves a rotation with no
usable secret. They stay masked by default, so a log or a shared transcript
never holds them; ``--reveal`` prints them, the way ``client-app create`` shows
its token.
"""

from __future__ import annotations

REVEAL_FLAG = "--reveal"

#: The commands that print their credential when given ``--reveal``.
REVEAL_COMMANDS = frozenset(
    {
        "dashboard.embed.secret.rotate",
        "dashboard.embed.preview-token.create",
    }
)
