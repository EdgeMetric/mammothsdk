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
import threading
import typing
from collections.abc import Iterator
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


def _declared(op: dict[str, Any], location: str) -> set[str]:
    return {p["name"] for p in op.get("parameters", []) if p.get("in") == location}


def test_generated_method_inventory_matches_the_module() -> None:
    defined = {
        n for n, v in vars(gen).items() if inspect.iscoroutinefunction(v) and not n.startswith("_")
    }
    assert set(gen.GENERATED_METHODS) == defined
    assert len(gen.GENERATED_METHODS) == len(set(gen.GENERATED_METHODS))


@pytest.mark.parametrize("name", gen.GENERATED_METHODS)
async def test_generated_method_hits_a_spec_operation(
    name: str, server: RecordingServer, client: MammothClient
) -> None:
    fn = getattr(client.dashboards, name)
    kwargs, _ = _call_args(getattr(gen, name), with_optionals=False)
    await fn(**kwargs)

    sent = server.requests[-1]
    ops = _matching_ops(str(sent["method"]), str(sent["path"]))
    assert ops, f"{name}: {sent['method']} {sent['path']} is not an operation in the pinned spec"
    # A literal segment can satisfy a "{placeholder}" of another operation (".../analytics" vs
    # ".../{dashboard_id}"), so every argument that names a placeholder must be in the path.
    templates = _matching_templates(str(sent["method"]), str(sent["path"]))
    segments = str(sent["path"]).split("/")
    for arg, value in kwargs.items():
        if arg != "body" and any("{" + arg + "}" in t for t in templates):
            assert (
                str(value) in segments
            ), f"{name}: `{arg}`={value!r} is missing from {sent['path']}"
    # Optional query args are omitted; whatever is sent must be declared and every
    # required query parameter of the operation must be sent.
    declared: set[str] = set().union(*(_declared(op, "query") for op in ops))
    assert set(sent["query"]) <= declared, (name, sent["query"], declared)
    if len(ops) == 1:
        required = {
            p["name"]
            for p in ops[0].get("parameters", [])
            if p.get("in") == "query" and p.get("required")
        }
        assert required <= set(sent["query"]), (name, required, sent["query"])
    # A body is only sent for operations that declare one.
    if sent["body"] is not None:
        assert any("requestBody" in op for op in ops), f"{name}: sends a body, spec has none"
    # A spec operation with a required body must get one from the method.
    if all(op.get("requestBody", {}).get("required") for op in ops):
        assert sent["body"] is not None, f"{name}: spec requires a body, none sent"


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
