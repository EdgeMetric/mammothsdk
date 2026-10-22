"""``server_status``: which commands the production server serves, derived from the pinned specs."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from mammoth_cli.commands import capability, schema
from mammoth_cli.context import resolver
from mammoth_cli.context.resolver import ExplicitLogin
from mammoth_cli.embed import invoke
from mammoth_cli.errors.envelope import EXIT_USAGE, pending_server_release_error
from mammoth_cli.manifest import loader
from mammoth_cli.runtime import embedded
from mammoth_cli.services import factory as service_factory
from mammoth_cli.services.testing import FakeMammothService

CLI_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CLI_ROOT / "scripts"))

import build_server_status as derivation  # noqa: E402

PENDING = "automation.runs"  # route on server master, not in the pinned prod spec
SERVED = "project.list"


@pytest.fixture
def login(monkeypatch: pytest.MonkeyPatch) -> ExplicitLogin:
    monkeypatch.setattr(resolver, "resolve_token_workspace", lambda *_args: 7)
    monkeypatch.setattr(
        service_factory, "build_service", lambda *_args, **_kwargs: FakeMammothService()
    )
    return ExplicitLogin(
        api_key=None,
        api_secret=None,
        api_token="jwt",
        server_prefix="box",
        headers={"Authorization": "Bearer jwt"},
    )


# --- derivation --------------------------------------------------------------


def test_classify_uses_prod_and_master_routes() -> None:
    prod = {("GET", "/a"), ("GET", "/gone")}
    master = {("GET", "/a"), ("GET", "/new")}
    assert derivation.classify(prod, master, {("GET", "/a")}) == "served"
    assert derivation.classify(prod, master, {("GET", "/a"), ("GET", "/new")}) == "pending"
    assert derivation.classify(prod, master, {("GET", "/gone")}) == "removed_on_server"
    # A template route in neither spec says nothing; a command with no route is served.
    assert derivation.classify(prod, master, {("POST", "/x/{}/{}")}) == "served"
    assert derivation.classify(prod, master, set()) == "served"


def test_a_known_pending_command_is_pending_and_a_common_one_is_served() -> None:
    document = derivation.derive()["commands"]
    assert document[PENDING]["server_status"] == "pending"
    assert SERVED not in document
    assert loader.server_status(PENDING) == "pending"
    assert loader.server_status(SERVED) == "served"
    assert loader.server_status("no.such.command") == "served"


def test_the_pinned_prod_spec_is_the_production_server() -> None:
    meta = json.loads((derivation.OPENAPI_DIR / "metadata.json").read_text(encoding="utf-8"))
    assert derivation.PROD_HOST in meta["source_url"]


def test_server_status_file_is_fresh() -> None:
    expected = derivation.render(derivation.derive())
    assert derivation.OUTPUT.read_text(encoding="utf-8") == expected, (
        "stale: run `python scripts/build_server_status.py` "
        "(scripts/build_manifests.py runs it too)"
    )


def test_check_flag_passes_when_fresh() -> None:
    done = subprocess.run(
        [sys.executable, str(CLI_ROOT / "scripts" / "build_server_status.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stderr


def test_compiled_manifest_carries_the_derived_status() -> None:
    derived = {cid: item["server_status"] for cid, item in derivation.derive()["commands"].items()}
    compiled = {
        record["command_id"]: record["server_status"]
        for record in loader.load_commands()
        if "server_status" in record
    }
    assert compiled == derived
    assert set(compiled.values()) <= {"pending", "removed_on_server"}


# --- discovery ---------------------------------------------------------------


def test_schema_get_brief_and_full_carry_the_status() -> None:
    pending = schema.get_schema(PENDING) or {}
    assert pending["server_status"] == "pending"
    assert (schema.get_schema(SERVED) or {})["server_status"] == "served"
    assert schema.brief_schema(pending)["server_status"] == "pending"


def test_schema_list_and_find_rows_carry_the_status() -> None:
    family = schema.schema_index("automation")["commands"]
    assert {row["command_id"]: row["server_status"] for row in family}[PENDING] == "pending"
    found = schema.find_schemas("automation runs")["matches"]
    assert {row["command_id"]: row["server_status"] for row in found}[PENDING] == "pending"
    assert any(e["command_id"] == PENDING for e in schema.schema_entries())


def test_capability_entries_carry_the_status() -> None:
    entries = capability.capability_entries()
    by_command = {e["canonical_command"]: e for e in entries}
    assert by_command[SERVED]["server_status"] == "served"
    assert all(e["server_status"] in {None, "served"} for e in entries)
    # The capability table is one row per operation in the pinned prod spec, so a command
    # whose route is only on master has no row there until prod serves it.
    assert PENDING not in by_command


# --- embed opt-in --------------------------------------------------------------


def test_hide_pending_hides_pending_commands_from_discovery(login: ExplicitLogin) -> None:
    call = embedded.EmbeddedCall(login=login, hide_pending=True)
    token = embedded.enter(call)
    try:
        assert all(e["command_id"] != PENDING for e in schema.schema_entries())
        family = schema.schema_index("automation")["commands"]
        assert all(row["command_id"] != PENDING for row in family)
        found = schema.find_schemas("automation runs")
        assert all(row["command_id"] != PENDING for row in found["matches"])
        assert capability.hidden_pending({"server_status": "pending"})
        assert not capability.hidden_pending({"server_status": "served"})
    finally:
        embedded.leave(token)
    # Outside an opted-in call nothing is hidden.
    assert any(e["command_id"] == PENDING for e in schema.schema_entries())


def test_embedded_call_refuses_a_pending_command_only_when_asked(login: ExplicitLogin) -> None:
    args = ["automation", "runs", "123", "--project", "1"]
    refused: dict[str, Any] = invoke(args, login=login, hide_pending=True)
    assert refused["error"]["code"] == "pending_server_release"
    assert pending_server_release_error("automation runs").exit_status == EXIT_USAGE
    assert "automation runs" in refused["error"]["message"]
    default: dict[str, Any] = invoke(args, login=login)
    assert default.get("error", {}).get("code") != "pending_server_release"


def test_hide_pending_leaves_served_commands_alone(login: ExplicitLogin) -> None:
    envelope = invoke(["project", "list"], login=login, hide_pending=True)
    assert envelope.get("error", {}).get("code") != "pending_server_release"
