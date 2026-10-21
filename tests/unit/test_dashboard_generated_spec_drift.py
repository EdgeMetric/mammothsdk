"""Every generated dashboard method must hit an operation that exists in the pinned spec.

For each name in ``GENERATED_METHODS`` the method is called on a real client against a
recording loopback server. The recorded HTTP method + path must match an operation of the
pinned prod OpenAPI spec (``mammoth-cli/spec/openapi/openapi.json``); query parameters that
were sent must be declared by that operation, and a JSON body must only be sent where the
operation declares a request body. This catches generator drift without trusting the
generator's own tables.
"""

from __future__ import annotations

import inspect
import re
import sys
import threading
import typing
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from mammoth.api import dashboard_generated as gen
from mammoth.client import MammothClient

from ._loopback import RecordingServer
from ._spec import spec


@pytest.fixture(scope="module")
def _module_server() -> Iterator[RecordingServer]:
    # One loopback server for the ~100 generated methods: per-test shutdown costs 0.5s each.
    srv = RecordingServer()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()


@pytest.fixture
def server(_module_server: RecordingServer) -> RecordingServer:
    _module_server.requests.clear()
    return _module_server


@pytest.fixture
def client(server: RecordingServer) -> MammothClient:
    c = MammothClient(
        "key",
        "secret",
        workspace_id=1,
        base_url=f"http://127.0.0.1:{server.server_port}/api/v2",
        allow_insecure_loopback_http=True,
    )
    c.set_project_id(25654)
    return c


_OPS = [
    (m.upper(), path, op)
    for path, item in spec()["paths"].items()
    for m, op in item.items()
    if m in ("get", "post", "put", "patch", "delete")
]


def _template_regex(path: str) -> re.Pattern[str]:
    return re.compile(
        "^"
        + re.sub(r"\{[^}]+\}", r"[^/]+", re.escape(path).replace(r"\{", "{").replace(r"\}", "}"))
        + "$"
    )


_COMPILED = [(m, path, op, _template_regex(path)) for m, path, op in _OPS]


def _matching_ops(method: str, concrete_path: str) -> list[dict[str, Any]]:
    return [op for m, _p, op, rx in _COMPILED if m == method and rx.match(concrete_path)]


def _matching_templates(method: str, concrete_path: str) -> list[str]:
    return [p for m, p, _op, rx in _COMPILED if m == method and rx.match(concrete_path)]


def _sample(annotation: Any, name: str) -> Any:
    """A plausible value for a parameter, chosen from its annotation."""
    origin = typing.get_origin(annotation)
    args = [a for a in typing.get_args(annotation) if a is not type(None)]
    if origin is typing.Literal:
        return args[0]
    if origin in (typing.Union, getattr(__import__("types"), "UnionType", None)):
        return _sample(args[0], name)
    if annotation is int:
        return 7
    if annotation is bool:
        return True
    if annotation is str:
        return "sample"
    if origin is list:
        return []
    return "sample"


def _call_args(fn: Any, *, with_optionals: bool) -> tuple[dict[str, Any], list[str]]:
    hints = typing.get_type_hints(fn, vars(gen))
    sig = inspect.signature(fn)
    kwargs: dict[str, Any] = {}
    optional_names: list[str] = []
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        if name == "body":
            kwargs[name] = {}  # dict bodies are forwarded verbatim by _json_body
        elif param.default is inspect.Parameter.empty:
            kwargs[name] = _sample(hints[name], name)
        else:
            optional_names.append(name)
            if with_optionals:
                kwargs[name] = _sample(hints[name], name)
    return kwargs, optional_names


def _expected_operations() -> dict[str, tuple[str, str, dict[str, Any]]]:
    """method name -> (HTTP method, path template, spec operation).

    Taken from the spec plus the CLI's reviewed operationId -> command table
    (``mammoth-cli/scripts/_command_map.py``), the same mapping the generator reads. Neither
    is the SDK's own ``GENERATED_METHODS`` list or its path strings.
    """
    scripts = str(Path(__file__).resolve().parents[2] / "mammoth-cli" / "scripts")
    sys.path.insert(0, scripts)
    try:
        from _command_map import OVERRIDES
    finally:
        sys.path.remove(scripts)
    found: dict[str, tuple[str, str, dict[str, Any]]] = {}
    for path, item in spec()["paths"].items():
        for method, op in item.items():
            command = OVERRIDES.get(op.get("operationId", "")) if method in _METHODS else None
            if command and command.startswith("dashboard."):
                name = command.removeprefix("dashboard.").replace(".", "_").replace("-", "_")
                assert name not in found, f"two operations map to {name}"
                found[name] = (method.upper(), path, op)
    return found


_METHODS = ("get", "post", "put", "patch", "delete")
EXPECTED = _expected_operations()


def _declared(op: dict[str, Any], location: str) -> set[str]:
    return {p["name"] for p in op.get("parameters", []) if p.get("in") == location}


def test_generated_methods_are_exactly_the_non_handwritten_dashboard_operations() -> None:
    generated = set(gen.GENERATED_METHODS)
    assert len(gen.GENERATED_METHODS) == len(generated)
    assert generated <= set(EXPECTED), sorted(generated - set(EXPECTED))
    # Every other dashboard operation of the spec must be a hand-written DashboardsAPI method.
    from mammoth.api import dashboards as hand

    handwritten = {
        name
        for name in set(EXPECTED) - generated
        if getattr(getattr(hand.DashboardsAPI, name, None), "__module__", None) == hand.__name__
    }
    assert set(EXPECTED) - generated == handwritten, sorted(set(EXPECTED) - generated - handwritten)
    assert {n for n, v in vars(gen).items() if inspect.iscoroutinefunction(v)} - {
        n for n in vars(gen) if n.startswith("_")
    } == generated


@pytest.mark.parametrize("name", gen.GENERATED_METHODS)
async def test_generated_method_hits_its_own_spec_operation(
    name: str, server: RecordingServer, client: MammothClient
) -> None:
    http_method, template, op = EXPECTED[name]
    kwargs, _ = _call_args(getattr(gen, name), with_optionals=False)
    await getattr(client.dashboards, name)(**kwargs)

    sent = server.requests[-1]
    assert (sent["method"], _template_regex(template).match(str(sent["path"])) is not None) == (
        http_method,
        True,
    ), f"{name}: sent {sent['method']} {sent['path']}, spec operation is {http_method} {template}"
    # A literal segment can also satisfy another "{placeholder}", so every argument that
    # names a placeholder of this operation must appear in the path as given.
    segments = str(sent["path"]).split("/")
    for arg, value in kwargs.items():
        if arg != "body" and "{" + arg + "}" in template:
            assert str(value) in segments, f"{name}: `{arg}`={value!r} missing from {sent['path']}"
    # Optional query args are omitted; whatever is sent must be declared and every
    # required query parameter of the operation must be sent.
    assert set(sent["query"]) <= _declared(op, "query"), (name, sent["query"])
    required = {
        p["name"] for p in op.get("parameters", []) if p.get("in") == "query" and p.get("required")
    }
    assert required <= set(sent["query"]), (name, required, sent["query"])
    # A body is only sent when the operation declares one, and a required body is always sent.
    body_spec = op.get("requestBody")
    if sent["body"] is not None:
        assert body_spec, f"{name}: sends a body, the spec operation has none"
        props = _body_properties(body_spec)
        if props is not None and isinstance(sent["body"], dict):
            assert set(sent["body"]) <= props, (name, set(sent["body"]) - props)
    if body_spec and body_spec.get("required"):
        assert sent["body"] is not None, f"{name}: spec requires a body, none sent"


def _body_properties(body_spec: dict[str, Any]) -> set[str] | None:
    """Property names of a JSON request body schema, or None when it is not a plain object."""
    content = body_spec.get("content", {}).get("application/json")
    if not content:
        return None
    node = content.get("schema", {})
    if "$ref" in node:
        node = spec()["components"]["schemas"][node["$ref"].rsplit("/", 1)[-1]]
    props = node.get("properties")
    return set(props) if props else None


@pytest.mark.parametrize("name", gen.GENERATED_METHODS)
async def test_generated_method_query_params_are_declared_in_spec(
    name: str, server: RecordingServer, client: MammothClient
) -> None:
    kwargs, optional = _call_args(getattr(gen, name), with_optionals=True)
    await getattr(client.dashboards, name)(**kwargs)

    sent = server.requests[-1]
    ops = _matching_ops(str(sent["method"]), str(sent["path"]))
    assert ops, f"{name}: {sent['method']} {sent['path']} is not in the pinned spec"
    declared: set[str] = set().union(*(_declared(op, "query") for op in ops))
    assert set(sent["query"]) <= declared, (name, sent["query"], declared)
    # Every optional argument the method accepts reaches the wire as a query param
    # unless it is the request body.
    assert set(sent["query"]) >= {n for n in optional if n != "body"}, name
