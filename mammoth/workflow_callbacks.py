"""Check the signature on a workflow run's callback.

A run started with ``WorkflowsAPI.start_run(..., callback_url=...)`` makes Mammoth POST a small
JSON to that URL when the run ends. The request carries::

    X-Mammoth-Signature: t=<unix seconds>,v1=<hex HMAC-SHA256 of "<t>.<body>">

keyed with the run's ``callback_secret``, which ``start_run`` returns once. Verify the raw body
bytes as received, before parsing them::

    from mammoth import verify_callback

    if not verify_callback(secret, request.headers["X-Mammoth-Signature"], raw_body):
        return 401

Pure: no network and no client.
"""

from __future__ import annotations

import hashlib
import hmac
import time

#: The request header that carries the signature.
SIGNATURE_HEADER = "X-Mammoth-Signature"
#: Seconds a signature's timestamp may differ from now (either way) by default.
DEFAULT_TOLERANCE = 300


def sign_callback(secret: str, timestamp: int, body: bytes | str) -> str:
    """Return the ``X-Mammoth-Signature`` value Mammoth sends for ``body`` at ``timestamp``.

    Args:
        secret: The run's ``callback_secret``.
        timestamp: Unix seconds.
        body: The request body, as bytes or UTF-8 text.

    Returns:
        ``t=<timestamp>,v1=<hex HMAC-SHA256>``.
    """
    raw = body.encode() if isinstance(body, str) else body
    mac = hmac.new(secret.encode(), f"{timestamp}.".encode() + raw, hashlib.sha256)
    return f"t={timestamp},v1={mac.hexdigest()}"


def callback_problem(
    secret: str,
    header: str,
    body: bytes | str,
    tolerance: int | None = DEFAULT_TOLERANCE,
    now: float | None = None,
) -> str | None:
    """Say why a callback's signature does not hold, or return None when it does.

    Args:
        secret: The run's ``callback_secret``.
        header: The ``X-Mammoth-Signature`` header value.
        body: The raw request body, as bytes or UTF-8 text.
        tolerance: Most seconds the header's timestamp may be from ``now``; None skips the
            check (not recommended: it lets an old request be replayed).
        now: Unix seconds to judge the timestamp against (default: the clock).

    Returns:
        None for a valid signature, else a short reason.
    """
    if not secret:
        return "the secret is empty"
    fields: dict[str, list[str]] = {}
    for part in (header or "").split(","):
        key, sep, value = part.strip().partition("=")
        if sep and value:
            fields.setdefault(key.strip(), []).append(value.strip())
    stamps = fields.get("t")
    if not stamps or len(stamps) != 1 or not stamps[0].isdigit():
        return "the header has no t=<unix seconds> timestamp"
    if not fields.get("v1"):
        return "the header has no v1 signature"
    timestamp = int(stamps[0])
    if tolerance is not None:
        clock = time.time() if now is None else now
        if abs(clock - timestamp) > tolerance:
            return f"the timestamp is more than {tolerance} seconds from now"
    expected = sign_callback(secret, timestamp, body).partition(",v1=")[2]
    if any(hmac.compare_digest(expected, given.lower()) for given in fields["v1"]):
        return None
    return "the signature does not match the body and secret"


def verify_callback(
    secret: str,
    header: str,
    body: bytes | str,
    tolerance: int | None = DEFAULT_TOLERANCE,
    now: float | None = None,
) -> bool:
    """Return True when a workflow run callback's signature is valid and fresh.

    Args:
        secret: The run's ``callback_secret`` (from ``WorkflowsAPI.start_run``).
        header: The ``X-Mammoth-Signature`` header value.
        body: The raw request body, as bytes or UTF-8 text, before any JSON parsing.
        tolerance: Most seconds the header's timestamp may be from now (default 300); None
            skips the check.
        now: Unix seconds to judge the timestamp against (default: the clock).

    Returns:
        True when the signature matches and the timestamp is within ``tolerance``.
    """
    return callback_problem(secret, header, body, tolerance=tolerance, now=now) is None
