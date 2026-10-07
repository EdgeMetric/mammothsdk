"""Browser sign-in (OAuth 2.0 authorization code + PKCE), device-code sign-in
(RFC 8628) and token refresh.

``mammoth auth login`` opens the Mammoth consent page, receives the code on a
loopback listener (RFC 8252), and exchanges it for a 1 h ``mm_`` access token
plus a rotating refresh token. The CLI is a public client: it holds no secret.

``mammoth auth login --device`` is for a machine with no browser: it prints a
short code and a URL to open on any other device, then polls the token endpoint
until the code is approved, denied or expired.

The refresh token rotates on every use, and replaying an already-used one
revokes the whole connection on the server. Two CLI processes must therefore
never refresh at once: :func:`refresh_session` takes a file lock, re-reads the
stored session once it holds the lock, and refreshes only if that session is
still near expiry.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import html
import http.server
import os
import secrets
import threading
import time
import urllib.parse
import webbrowser
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from mammoth import oauth as sdk_oauth
from mammoth_cli.context import credentials
from mammoth_cli.context.credentials import OAuthSession
from mammoth_cli.context.endpoint import DEFAULT_SERVER_PREFIX
from mammoth_cli.context.profiles import config_dir
from mammoth_cli.errors.envelope import EXIT_AUTH, EXIT_USAGE, CliError

#: The first-party CLI's OAuth client id, one constant per environment (the
#: server prefix). The server allow-lists these ids, so they are not
#: configurable at run time. An environment absent here has no CLI client yet.
OAUTH_CLIENT_IDS: dict[str, str] = {
    "challenger": "oc_aea5c2ce829da3f8",
    "koyal": "oc_f2566336e235795c",
}

#: Refresh when the access token has less than this long to live.
REFRESH_MARGIN_SECONDS = 120
CALLBACK_PATH = "/callback"
LOGIN_TIMEOUT_SECONDS = 300.0
_LOCK_POLL_SECONDS = 0.1
_LOCK_WAIT_SECONDS = 60.0

CODE_LOGIN_EXPIRED = "login_expired"
CODE_OAUTH_UNAVAILABLE = "oauth_unavailable"
CODE_OAUTH_LOGIN_FAILED = "oauth_login_failed"
CODE_DEVICE_LOGIN_EXPIRED = "device_login_expired"

#: RFC 8628 §3.4: the grant type the device sign-in polls with.
DEVICE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
#: RFC 8628 §3.5: a slow_down answer adds this many seconds to the interval.
SLOW_DOWN_STEP_SECONDS = 5
#: Added to every wait so a poll never lands a hair before the server's interval.
POLL_MARGIN_SECONDS = 1.0


def login_expired_error() -> CliError:
    """The stable error for a session that can no longer be refreshed."""
    return CliError(
        code=CODE_LOGIN_EXPIRED,
        message="Login expired, run `mammoth auth login`.",
        exit_status=EXIT_AUTH,
        hint="Your browser sign-in is no longer valid. Sign in again.",
        recovery_commands=["mammoth auth login"],
    )


def has_client_id(server_prefix: str | None) -> bool:
    """Whether the CLI has an OAuth client registered for this environment."""
    return (
        server_prefix if server_prefix is not None else DEFAULT_SERVER_PREFIX
    ) in OAUTH_CLIENT_IDS


def client_id_for(server_prefix: str | None) -> str:
    """Return the CLI's OAuth client id for one environment.

    Raises:
        CliError: ``oauth_unavailable`` when the environment has no CLI client.
    """
    prefix = server_prefix if server_prefix is not None else DEFAULT_SERVER_PREFIX
    try:
        return OAUTH_CLIENT_IDS[prefix]
    except KeyError:
        raise CliError(
            code=CODE_OAUTH_UNAVAILABLE,
            message=f"Browser sign-in is not available on '{prefix}' yet.",
            exit_status=EXIT_USAGE,
            hint="Paste an API token instead: mammoth auth login --method token",
            recovery_commands=["mammoth auth login --method token"],
        ) from None


# --- PKCE ---------------------------------------------------------------------


def new_pkce_pair() -> tuple[str, str]:
    """Return ``(code_verifier, S256 code_challenge)``."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def authorize_url(
    base_url: str, *, client_id: str, redirect_uri: str, challenge: str, state: str
) -> str:
    """Build the consent-page URL for one login attempt."""
    query = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
        }
    )
    return f"{base_url}/oauth/authorize?{query}"


# --- loopback listener ----------------------------------------------------------

_PAGE = (
    "<!doctype html><meta charset=utf-8><title>Mammoth CLI</title>"
    "<body style='font-family:system-ui;margin:3rem'><h2>{title}</h2><p>{body}</p>"
)


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - http.server's naming
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path != CALLBACK_PATH:
            self.send_error(404)
            return
        params = {k: v[0] for k, v in urllib.parse.parse_qs(parsed.query).items()}
        server = self.server
        assert isinstance(server, _CallbackServer)
        server.params = params
        failed = "error" in params or "code" not in params
        title = "Sign-in failed" if failed else "Signed in"
        body = (
            "Return to the terminal for details."
            if failed
            else "You can close this tab and return to the terminal."
        )
        payload = _PAGE.format(title=html.escape(title), body=html.escape(body)).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


class _CallbackServer(http.server.HTTPServer):
    params: dict[str, str] | None = None


@contextlib.contextmanager
def loopback_listener() -> Iterator[_CallbackServer]:
    """Listen on 127.0.0.1 on a random free port, for one callback."""
    server = _CallbackServer(("127.0.0.1", 0), _CallbackHandler)
    try:
        yield server
    finally:
        server.server_close()


def redirect_uri_for(server: _CallbackServer) -> str:
    return f"http://127.0.0.1:{server.server_port}{CALLBACK_PATH}"


def wait_for_callback(server: _CallbackServer, timeout: float) -> dict[str, str]:
    """Serve requests until the callback arrives, or raise on timeout."""
    deadline = time.monotonic() + timeout
    server.timeout = 1.0
    while server.params is None:
        if time.monotonic() >= deadline:
            raise CliError(
                code=CODE_OAUTH_LOGIN_FAILED,
                message="Timed out waiting for the browser sign-in.",
                exit_status=EXIT_AUTH,
                hint="Run `mammoth auth login` again and approve the request in the browser.",
                recovery_commands=["mammoth auth login"],
            )
        server.handle_request()
    return server.params


def check_callback(params: dict[str, str], *, state: str, issuer: str) -> str:
    """Validate the redirect's ``state`` (and RFC 9207 ``iss``); return the code.

    Raises:
        CliError: ``oauth_login_failed`` on a denial, a state mismatch, a
            foreign issuer, or a missing code.
    """
    if "error" in params:
        detail = params.get("error_description") or params["error"]
        raise _login_failed(f"The sign-in was not approved: {detail}")
    if not secrets.compare_digest(params.get("state", ""), state):
        raise _login_failed("The sign-in response did not match this login attempt (state).")
    if "iss" in params and params["iss"] != issuer:
        raise _login_failed("The sign-in response came from an unexpected issuer.")
    if not params.get("code"):
        raise _login_failed("The sign-in response carried no authorization code.")
    return params["code"]


def _login_failed(message: str) -> CliError:
    return CliError(
        code=CODE_OAUTH_LOGIN_FAILED,
        message=message,
        exit_status=EXIT_AUTH,
        hint="Run `mammoth auth login` again.",
        recovery_commands=["mammoth auth login"],
    )


# --- token endpoint -------------------------------------------------------------


@dataclass(frozen=True)
class TokenGrant:
    """The parsed answer of the token endpoint."""

    access: str
    refresh: str
    expires_in: int
    workspace_id: int | None = None
    project_id: int | None = None


def _post_token(base_url: str, form: dict[str, str]) -> tuple[int, dict[str, object]]:
    try:
        status, body = sdk_oauth.token_request(base_url, form)
    except sdk_oauth.OAuthTransportError as exc:
        raise CliError(
            code="network_error",
            message="Could not reach Mammoth's sign-in service.",
            exit_status=EXIT_AUTH,
            hint="Check your connection and try again.",
        ) from exc
    return status, body if isinstance(body, dict) else {}


def _optional_id(value: object) -> int | None:
    return None if value is None else int(str(value))


def _parse_grant(body: dict[str, object]) -> TokenGrant:
    try:
        return TokenGrant(
            access=str(body["access_token"]),
            refresh=str(body["refresh_token"]),
            expires_in=int(str(body["expires_in"])),
            workspace_id=_optional_id(body.get("workspace_id")),
            project_id=_optional_id(body.get("project_id")),
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise _login_failed("Mammoth's sign-in service returned an unreadable answer.") from exc


def exchange_code(
    base_url: str, *, client_id: str, code: str, verifier: str, redirect_uri: str
) -> TokenGrant:
    """Trade the authorization code for tokens."""
    status, body = _post_token(
        base_url,
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "code_verifier": verifier,
        },
    )
    if status != 200:
        raise _login_failed(f"Mammoth refused the sign-in (HTTP {status}).")
    return _parse_grant(body)


def grant_id_from_refresh_token(refresh_token: str) -> int | None:
    """The server connection id: the leading segment of ``<id>.<random>.<mac>``."""
    head = refresh_token.split(".", 1)[0]
    return int(head) if head.isdigit() else None


def session_from_grant(grant: TokenGrant, client_id: str, now: float | None = None) -> OAuthSession:
    issued = int(now if now is not None else time.time())
    return OAuthSession(
        access=grant.access,
        refresh=grant.refresh,
        expires_at=issued + grant.expires_in,
        client_id=client_id,
        grant_id=grant_id_from_refresh_token(grant.refresh),
        workspace_id=grant.workspace_id,
        project_id=grant.project_id,
    )


def browser_login(
    base_url: str,
    *,
    client_id: str,
    open_browser: bool,
    say: Callable[[str], None],
    timeout: float = LOGIN_TIMEOUT_SECONDS,
) -> OAuthSession:
    """Run one PKCE loopback sign-in and return the resulting session."""
    verifier, challenge = new_pkce_pair()
    state = secrets.token_urlsafe(24)
    with loopback_listener() as server:
        redirect_uri = redirect_uri_for(server)
        url = authorize_url(
            base_url,
            client_id=client_id,
            redirect_uri=redirect_uri,
            challenge=challenge,
            state=state,
        )
        opened = open_browser and webbrowser.open(url)
        if opened:
            say("Opening your browser to sign in to Mammoth.")
        say(f"If it does not open, visit:\n  {url}")
        say(f"Waiting for approval on {redirect_uri} ...")
        params = wait_for_callback(server, timeout)
    code = check_callback(params, state=state, issuer=base_url)
    grant = exchange_code(
        base_url, client_id=client_id, code=code, verifier=verifier, redirect_uri=redirect_uri
    )
    return session_from_grant(grant, client_id)


# --- device code (RFC 8628) -----------------------------------------------------


@dataclass(frozen=True)
class DeviceChallenge:
    """What the server issues to start a device sign-in."""

    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str
    expires_in: int
    interval: int


def parse_device_challenge(body: dict[str, object]) -> DeviceChallenge:
    """Read the device-authorization answer; an unreadable one is a failed login."""
    try:
        return DeviceChallenge(
            device_code=str(body["device_code"]),
            user_code=str(body["user_code"]),
            verification_uri=str(body["verification_uri"]),
            verification_uri_complete=str(body.get("verification_uri_complete") or ""),
            expires_in=int(str(body["expires_in"])),
            interval=int(str(body["interval"])),
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise _login_failed("Mammoth's sign-in service returned an unreadable answer.") from exc


def start_device_login(base_url: str, *, client_id: str) -> DeviceChallenge:
    """Ask Mammoth for a device code and the code the person will type."""
    try:
        status, body = sdk_oauth.device_authorization_request(base_url, {"client_id": client_id})
    except sdk_oauth.OAuthTransportError as exc:
        raise CliError(
            code="network_error",
            message="Could not reach Mammoth's sign-in service.",
            exit_status=EXIT_AUTH,
            hint="Check your connection and try again.",
        ) from exc
    if status != 200 or not isinstance(body, dict):
        raise _login_failed(f"Mammoth refused to start a device sign-in (HTTP {status}).")
    return parse_device_challenge(body)


def read_poll(status: int, body: dict[str, object], interval: int) -> TokenGrant | int:
    """Interpret one poll answer.

    Returns the tokens once approved, or the seconds to wait before the next
    poll (longer after ``slow_down``).

    Raises:
        CliError: ``oauth_login_failed`` when the person denied the sign-in or
            the answer is not one RFC 8628 lets the client retry on;
            ``device_login_expired`` when the code ran out.
    """
    if status == 200:
        return _parse_grant(body)
    error = str(body.get("error", ""))
    if error == "authorization_pending":
        return interval
    if error == "slow_down":
        return interval + SLOW_DOWN_STEP_SECONDS
    if error == "access_denied":
        raise _login_failed("The sign-in was denied in the browser.")
    if error == "expired_token":
        raise device_login_expired_error()
    raise _login_failed(f"Mammoth refused the sign-in ({error or f'HTTP {status}'}).")


def device_login_expired_error() -> CliError:
    return CliError(
        code=CODE_DEVICE_LOGIN_EXPIRED,
        message="The sign-in code expired before it was approved.",
        exit_status=EXIT_AUTH,
        hint="Run `mammoth auth login --device` again and approve the new code.",
        recovery_commands=["mammoth auth login --device"],
    )


def device_login(base_url: str, *, client_id: str, say: Callable[[str], None]) -> OAuthSession:
    """Run one device sign-in: print the code, poll until it is approved."""
    challenge = start_device_login(base_url, client_id=client_id)
    say(f"To sign in, open {challenge.verification_uri} on any device and enter:")
    say(f"  {challenge.user_code}")
    if challenge.verification_uri_complete:
        say(f"Or open this link directly:\n  {challenge.verification_uri_complete}")
    say("Waiting for approval ...")
    deadline = time.monotonic() + challenge.expires_in
    interval = challenge.interval
    while time.monotonic() < deadline:
        time.sleep(interval + POLL_MARGIN_SECONDS)
        status, body = _post_token(
            base_url,
            {
                "grant_type": DEVICE_GRANT_TYPE,
                "device_code": challenge.device_code,
                "client_id": client_id,
            },
        )
        step = read_poll(status, body, interval)
        if isinstance(step, TokenGrant):
            return session_from_grant(step, client_id)
        interval = step
    raise device_login_expired_error()


# --- refresh under a file lock ----------------------------------------------------


@contextlib.contextmanager
def _file_lock(profile: str) -> Iterator[None]:
    """Hold an exclusive cross-process lock for one profile's refresh."""
    directory = config_dir()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = directory / f".oauth-{profile}.lock"
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    deadline = time.monotonic() + _LOCK_WAIT_SECONDS
    try:
        while not _try_lock(fd):
            if time.monotonic() >= deadline:
                raise CliError(
                    code="lock_timeout",
                    message="Another mammoth command is refreshing the login and did not finish.",
                    exit_status=EXIT_AUTH,
                    hint="Try the command again.",
                )
            time.sleep(_LOCK_POLL_SECONDS)
        try:
            yield
        finally:
            _unlock(fd)
    finally:
        os.close(fd)


def _try_lock(fd: int) -> bool:
    if os.name == "posix":
        import fcntl

        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        return True
    import msvcrt

    try:
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)  # type: ignore[attr-defined]
    except OSError:
        return False
    return True


def _unlock(fd: int) -> None:
    if os.name == "posix":
        import fcntl

        fcntl.flock(fd, fcntl.LOCK_UN)
    else:
        import msvcrt

        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]


def is_fresh(session: OAuthSession, now: float | None = None) -> bool:
    """True while the access token has more than the refresh margin left."""
    return session.expires_at - (now if now is not None else time.time()) > REFRESH_MARGIN_SECONDS


def _stored_session(profile: str) -> OAuthSession:
    credential = credentials.load_credential(profile)
    if credential is None or credential.oauth is None:
        raise login_expired_error()
    return credential.oauth


def refresh_session(profile: str, base_url: str) -> OAuthSession:
    """Return a session with a fresh access token, refreshing under the lock.

    Raises:
        CliError: ``login_expired`` when the server refuses the refresh token
            (expired, revoked, or already used).
    """
    with _file_lock(profile):
        # Another process may have refreshed while this one waited.
        session = _stored_session(profile)
        if is_fresh(session):
            return session
        status, body = _post_token(
            base_url,
            {
                "grant_type": "refresh_token",
                "refresh_token": session.refresh,
                "client_id": session.client_id,
            },
        )
        if status in (400, 401):
            raise login_expired_error()
        if status != 200:
            raise _login_failed(f"Mammoth refused the refresh (HTTP {status}).")
        renewed = session_from_grant(_parse_grant(body), session.client_id)
        credentials.replace_oauth_session(profile, renewed)
        return renewed


class TokenSource:
    """Callable that returns the current access token, refreshing when due.

    Passed to the SDK as ``token_provider`` so every request carries a fresh
    token. The token is cached in memory; the stored session is read again
    only when the cached one nears expiry.
    """

    def __init__(self, profile: str, base_url: str, session: OAuthSession) -> None:
        self._profile = profile
        self._base_url = base_url
        self._session = session
        self._guard = threading.Lock()

    def __call__(self) -> str:
        with self._guard:
            if not is_fresh(self._session):
                self._session = refresh_session(self._profile, self._base_url)
            return self._session.access


def token_source(profile: str, base_url: str) -> TokenSource:
    """Build a :class:`TokenSource` for a stored session, refreshing it now if due.

    Raises:
        CliError: ``login_expired`` when the stored session cannot be refreshed.
    """
    source = TokenSource(profile, base_url, _stored_session(profile))
    source()
    return source


# --- logout -----------------------------------------------------------------------


def revoke_grant(base_url: str, session: OAuthSession) -> str | None:
    """Ask the server to drop this connection. Return a warning, or None on success."""
    if session.grant_id is None:
        return "The server connection id is unknown, so it was not revoked on the server."
    try:
        status = sdk_oauth.revoke_grant(base_url, session.grant_id, session.access)
    except sdk_oauth.OAuthTransportError:
        return "Could not reach Mammoth to revoke the connection on the server."
    if status in (200, 204):
        return None
    return (
        f"Mammoth did not revoke the connection on the server (HTTP {status}). "
        "Remove it under Settings -> Connected apps."
    )
