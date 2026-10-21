"""``conditional_format_replace`` against a loopback server that keeps the rules it is given."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

import pytest

from mammoth.client import MammothClient
from mammoth.exceptions import MammothAPIError, MammothValidationError

RULE = {"cf_type": "RULE", "payload": {"FORMAT": {"applies_to": "row"}, "CONDITION": {}}}


class _RuleStore(HTTPServer):
    """Holds a dataview's rules by id, like the conditional-format route does."""

    def __init__(self, rules: dict[str, dict[str, object]]) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.rules = rules
        self.calls: list[str] = []
        self.fail_create_after: int | None = None
        self._next = len(rules)


class _Handler(BaseHTTPRequestHandler):
    server: _RuleStore

    def _reply(self, status: int, body: object) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def do_GET(self) -> None:  # noqa: N802
        self.server.calls.append("GET")
        self._reply(200, self.server.rules)

    def do_DELETE(self) -> None:  # noqa: N802
        rule_id = parse_qs(urlsplit(self.path).query)["rule_id"][0]
        self.server.calls.append(f"DELETE {rule_id}")
        self.server.rules.pop(rule_id)
        self._reply(200, {"deleted": rule_id})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        rule = json.loads(self.rfile.read(length))
        self.server.calls.append("POST")
        limit = self.server.fail_create_after
        if limit is not None and len(self.server.calls) > limit:
            self._reply(400, {"message": "bad rule", "error_code": "X"})
            return
        self.server._next += 1
        self.server.rules[f"new{self.server._next}"] = rule
        self._reply(200, self.server.rules)

    def log_message(self, *args: object) -> None:
        return


@pytest.fixture
def store() -> Iterator[_RuleStore]:
    srv = _RuleStore({"old1": dict(RULE), "old2": dict(RULE)})
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()


@pytest.fixture
def client(store: _RuleStore) -> MammothClient:
    c = MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{store.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    c.set_project_id(25654)
    return c


async def test_replace_deletes_every_old_rule_then_creates_the_new_ones(
    client: MammothClient, store: _RuleStore
) -> None:
    result = await client.dataviews.conditional_format_replace(500, 42, [RULE, RULE, RULE])

    assert result["deleted_rule_ids"] == ["old1", "old2"]
    assert len(result["created_rule_ids"]) == 3
    assert set(store.rules) == set(result["created_rule_ids"])
    assert store.calls == ["GET", "DELETE old1", "DELETE old2", "POST", "POST", "POST"]


async def test_an_empty_replacement_deletes_nothing(
    client: MammothClient, store: _RuleStore
) -> None:
    with pytest.raises(MammothValidationError, match="at least one rule"):
        await client.dataviews.conditional_format_replace(500, 42, [])
    assert store.calls == []


async def test_a_refused_rule_reports_what_was_already_deleted_and_created(
    client: MammothClient, store: _RuleStore
) -> None:
    store.fail_create_after = 4  # GET + 2 DELETE + first POST succeed; the second POST is refused

    with pytest.raises(MammothAPIError) as excinfo:
        await client.dataviews.conditional_format_replace(500, 42, [RULE, RULE])

    assert excinfo.value.details["deleted_rule_ids"] == ["old1", "old2"]
    assert len(excinfo.value.details["created_rule_ids"]) == 1
