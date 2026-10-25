"""Handler output matches each command's declared ``output_schema`` (#315).

Every command with a declared schema is run through the real CLI, the real SDK and the real
handler on its manifest ``agent_example``. Only the HTTP layer is replaced: each request
gets a sample built from the OpenAPI ``200`` schema of the operation it hits (the stand-in
for a recorded response; the repository holds none). The envelope's ``data`` must then
validate against the declared schema.

A command that stops with an error on its example (it needs an input the example cannot
supply from a sampled response) is counted as unexercised, not as passing. ``FLOOR`` keeps
that count from growing unnoticed.
"""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from mammoth.client import MammothClient

from mammoth_cli.commands.schema import output_schema
from mammoth_cli.context import resolver
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.services import openapi_types
from mammoth_cli.services.openapi_types import openapi_response_schema_for
from mammoth_cli.testing import login_default_profile, make_runner

#: Declared commands whose example must run to a result and validate (reads, writes).
FLOOR_READS = 300
FLOOR_WRITES = 320

#: What the SDK returns for an artifact route (PNG, PDF, MP4, HTML): a description of the body.
_BINARY_BODY = {
    "content_type": "image/png",
    "size_bytes": 3,
    "sha256": "0" * 64,
    "content_base64": "AAAA",
}

#: Commands whose response is polymorphic in a way the sampler cannot build: the SDK's model
#: rewrites the sampled branch's discriminating values, so the sample matches no branch.
_UNSAMPLABLE = frozenset({"connector.ds-config.get"})

_PROJECT = "1"
_WORKSPACE = 4


def _operation_templates() -> list[tuple[str, re.Pattern[str], str]]:
    """List every OpenAPI operation as (method, path pattern, operation id).

    Returns:
        The operations, those with the fewest path parameters first so that a literal
        path such as ``/dashboards/email-updates`` wins over ``/dashboards/{id}``.
    """
    found = []
    for path, item in openapi_types._document().get("paths", {}).items():
        pattern = re.compile("^" + re.sub(r"\{[^}]+\}", "[^/]+", path) + "$")
        for method, operation in item.items():
            if isinstance(operation, dict) and operation.get("operationId"):
                found.append((method.upper(), pattern, operation["operationId"]))
    found.sort(key=lambda entry: entry[1].pattern.count("[^/]+"))
    return found


_OPERATIONS = _operation_templates()


_STRING_FORMATS = {
    "date": "2026-01-01",
    "date-time": "2026-01-01T00:00:00Z",
    "email": "agent@example.com",
    "uuid": "00000000-0000-4000-8000-000000000001",
    "uri": "https://example.com",
}


def _full_sample(
    node: dict[str, Any], defs: dict[str, Any], seen: frozenset[str] = frozenset()
) -> Any:
    """Build a value for a schema with every property filled in.

    A sample with only the required keys would leave the SDK's typed models to dump their
    optional fields as ``null``, which a real server's response does not.

    Args:
        node: The schema node.
        defs: The schema's shared ``$defs``.
        seen: The ``$ref`` names being expanded, to stop a recursive schema.

    Returns:
        A JSON value the node accepts.
    """
    if "const" in node:
        return node["const"]
    if node.get("enum"):
        return node["enum"][0]
    ref = node.get("$ref")
    if isinstance(ref, str):
        name = ref.rsplit("/", 1)[-1]
        if name in seen:
            return {}
        return _full_sample(defs.get(name, {}), defs, seen | {name})
    if node.get("allOf"):
        merged: dict[str, Any] = {}
        for member in node["allOf"]:
            value = _full_sample(member, defs, seen)
            if isinstance(value, dict):
                merged.update(value)
        return merged
    for key in ("oneOf", "anyOf"):
        if node.get(key):
            return _full_sample(node[key][0], defs, seen)
    kind = node.get("type")
    if isinstance(kind, list):
        kind = next((item for item in kind if item != "null"), "null")
    if kind == "object" or "properties" in node:
        return {
            name: _full_sample(child, defs, seen)
            for name, child in node.get("properties", {}).items()
        }
    if kind == "array":
        return [_full_sample(node.get("items", {}), defs, seen)]
    scalars: dict[str | None, Any] = {"integer": 1, "number": 1.5, "boolean": True, "null": None}
    if kind in scalars:
        return scalars[kind]
    return _STRING_FORMATS.get(node.get("format"), "example")


def _spec_sample(method: str, endpoint: str) -> Any:
    """Build the response a spec-conforming server would give for one request.

    Args:
        method: HTTP method.
        endpoint: Request path, with or without a query string.

    Returns:
        A sample of the operation's ``200`` schema, or ``{}`` when the path is unknown.
    """
    path = "/" + endpoint.lstrip("/").split("?")[0]
    for verb, pattern, operation_id in _OPERATIONS:
        if verb == method.upper() and pattern.match(path):
            schema = openapi_response_schema_for((operation_id,))
            return _full_sample(schema, schema.get("$defs", {})) if schema else {}
    return {}


def _any_of(node: Any) -> Any:
    """Read every ``oneOf`` of a schema as ``anyOf``.

    The OpenAPI document uses ``oneOf`` over branches that overlap (a string and a
    date-time string, an IPv4 and an IPv6 address); a value that fits one of them is what
    it means, and ``oneOf`` would reject it for fitting two.

    Args:
        node: A schema, or part of one.

    Returns:
        A copy with ``oneOf`` renamed.
    """
    if isinstance(node, dict):
        return {("anyOf" if key == "oneOf" else key): _any_of(value) for key, value in node.items()}
    if isinstance(node, list):
        return [_any_of(item) for item in node]
    return node


def _declared() -> list[dict[str, Any]]:
    return sorted(
        (record for record in load_commands() if record.get("output_schema")),
        key=lambda record: record["command_id"],
    )


def _run(record: dict[str, Any]) -> dict[str, Any]:
    """Run a command's manifest example and return its JSON envelope.

    Args:
        record: The command's manifest record.

    Returns:
        The parsed envelope, or ``{"error": ...}`` when the output was not an envelope.
    """
    argv = shlex.split(record["agent_example"])[1:]
    argv += ["--output", "json", "--no-input", "--project", _PROJECT]
    if record["mutation_class"] != "read":
        argv.append("--yes")
    text = make_runner().invoke(argv).output.strip()
    try:
        return json.loads(text[text.find("{") :])  # type: ignore[no-any-return]
    except ValueError:
        return {"error": {"code": "not_json"}}


def test_declared_outputs_match_their_schemas(
    monkeypatch: pytest.MonkeyPatch,
    isolated_cli_config: Path,
    block_real_network: None,
    tmp_path: Path,
) -> None:
    login_default_profile()
    monkeypatch.chdir(tmp_path)

    async def fake_request(self: Any, method: str, endpoint: str, *args: Any, **kwargs: Any) -> Any:
        if kwargs.get("expected_response_shape") == "binary":
            return _BINARY_BODY
        return _spec_sample(method, endpoint)

    monkeypatch.setattr(MammothClient, "_request", fake_request)
    monkeypatch.setattr(resolver, "resolve_token_workspace", lambda *_args, **_kwargs: _WORKSPACE)

    failures: list[str] = []
    exercised = {"read": 0, "write": 0}
    for record in _declared():
        if record["command_id"] in _UNSAMPLABLE:
            continue
        envelope = _run(record)
        if "error" in envelope or "data" not in envelope:
            continue
        schema = output_schema(record)
        assert schema is not None, record["command_id"]
        errors = list(
            jsonschema.Draft202012Validator(_any_of(schema)).iter_errors(envelope["data"])
        )
        if errors:
            failures.append(f"{record['command_id']}: {errors[0].message[:200]}")
        exercised["read" if record["mutation_class"] == "read" else "write"] += 1

    assert not failures, "\n".join(failures)
    assert exercised["read"] >= FLOOR_READS, exercised
    assert exercised["write"] >= FLOOR_WRITES, exercised
