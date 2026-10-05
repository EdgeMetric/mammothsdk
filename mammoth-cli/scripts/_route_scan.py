#!/usr/bin/env python3
"""Static scan of the SDK for the HTTP routes each public method calls.

The SDK reaches the server only through ``client._request*("VERB", "/path")``.
This module reads those call sites from the source with ``ast`` (no import, no
network), so the coverage matrix can be derived from the code instead of from
hand-edited mapping fields. Path arguments are normalised: every f-string
placeholder and every OpenAPI ``{param}`` becomes ``{}``.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SDK_ROOT = REPO_ROOT / "mammoth"
REQUEST_METHODS = frozenset({"_request", "_request_json", "_request_binary", "_request_list"})
HTTP_VERBS = frozenset({"GET", "PUT", "POST", "DELETE", "PATCH", "HEAD", "OPTIONS"})
_PARAM = re.compile(r"\{[^{}]*\}")
_QUERY = re.compile(r"[?#].*$")


@dataclass(frozen=True)
class SdkCall:
    """One literal ``VERB path`` call site inside one SDK function."""

    method: str
    path: str
    sdk_symbol: str
    line: int


def normalize_path(path: str) -> str:
    """Return ``path`` with every ``{param}`` replaced by ``{}`` and no query string."""
    return _PARAM.sub("{}", _QUERY.sub("", path)).rstrip("/") or "/"


_GENERATED_MODULE = "mammoth.api.dashboard_generated"
_GENERATED_TARGET = "mammoth.api.dashboards.DashboardsAPI"
_MAX_DEPTH = 6

type _Function = ast.FunctionDef | ast.AsyncFunctionDef
type _Locals = dict[str, ast.expr]


class _Module:
    """Constants and helper functions of one SDK module, for path resolution."""

    def __init__(self, tree: ast.Module) -> None:
        self.constants: _Locals = {}
        self.functions: dict[str, _Function] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                self.functions.setdefault(node.name, node)
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name):
                    self.constants[target.id] = node.value

    def resolve(
        self, node: ast.expr, local: _Locals, bound: dict[str, str], depth: int = 0
    ) -> str | None:
        """Return the route template ``node`` evaluates to, ``{}`` for unknown parts."""
        if depth > _MAX_DEPTH:
            return None
        if isinstance(node, ast.Constant):
            return node.value if isinstance(node.value, str) else None
        if isinstance(node, ast.JoinedStr):
            return "".join(self._part(part, local, bound, depth) for part in node.values)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self.resolve(node.left, local, bound, depth + 1)
            right = self.resolve(node.right, local, bound, depth + 1)
            return None if left is None or right is None else left + right
        if isinstance(node, ast.Name):
            return self._name(node.id, local, bound, depth)
        if isinstance(node, ast.Call):
            return self._call(node, local, bound, depth)
        return None

    def _part(self, part: ast.expr, local: _Locals, bound: dict[str, str], depth: int) -> str:
        if isinstance(part, ast.Constant):
            return str(part.value)
        value = part.value if isinstance(part, ast.FormattedValue) else part
        resolved = self.resolve(value, local, bound, depth + 1)
        return "{}" if resolved is None else resolved

    def _name(self, name: str, local: _Locals, bound: dict[str, str], depth: int) -> str | None:
        if name in bound:
            return bound[name]
        if name in local:
            return self.resolve(local[name], {}, bound, depth + 1)
        if name in self.constants:
            return self.resolve(self.constants[name], {}, {}, depth + 1)
        return None

    def _call(
        self, node: ast.Call, local: _Locals, bound: dict[str, str], depth: int
    ) -> str | None:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "replace":
            return self.resolve(func.value, local, bound, depth + 1)
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        helper = self.functions.get(name or "")
        if helper is None:
            return None
        params = [a.arg for a in helper.args.args if a.arg != "self"]
        defaults = dict(
            zip(
                params[len(params) - len(helper.args.defaults) :], helper.args.defaults, strict=True
            )
        )
        args = {
            param: _or_hole(self.resolve(arg, local, bound, depth + 1))
            for param, arg in {**defaults, **dict(zip(params, node.args, strict=False))}.items()
        }
        returns = [n.value for n in ast.walk(helper) if isinstance(n, ast.Return) and n.value]
        if not returns:
            return None
        return self.resolve(returns[0], _locals(helper), args, depth + 1)


def _or_hole(resolved: str | None) -> str:
    """An unknown argument is a ``{}`` placeholder; an empty string stays empty."""
    return "{}" if resolved is None else resolved


def _locals(function: _Function) -> _Locals:
    """First simple ``name = value`` assignment per local name."""
    found: _Locals = {}
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                found.setdefault(target.id, node.value)
    return found


def _call_site(node: ast.Call, module: _Module, local: _Locals) -> tuple[str, str] | None:
    func = node.func
    if not (isinstance(func, ast.Attribute) and func.attr in REQUEST_METHODS):
        return None
    if len(node.args) < 2:
        return None
    verb = node.args[0]
    path = module.resolve(node.args[1], local, {})
    if not (isinstance(verb, ast.Constant) and isinstance(verb.value, str) and path):
        return None
    method = verb.value.upper()
    return (method, path) if method in HTTP_VERBS and path.startswith("/") else None


class _Visitor(ast.NodeVisitor):
    def __init__(self, module: str, resolver: _Module) -> None:
        self.module = module
        self.resolver = resolver
        self.scope: list[str] = []
        self.locals: list[_Locals] = []
        self.calls: list[SdkCall] = []

    def _function(self, node: _Function) -> None:
        self.scope.append(node.name)
        self.locals.append(_locals(node))
        self.generic_visit(node)
        self.locals.pop()
        self.scope.pop()

    visit_FunctionDef = visit_AsyncFunctionDef = _function  # noqa: N815

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_Call(self, node: ast.Call) -> None:
        site = _call_site(node, self.resolver, self.locals[-1] if self.locals else {})
        if site and self.scope:
            for symbol in self._symbols():
                self.calls.append(SdkCall(site[0], normalize_path(site[1]), symbol, node.lineno))
        self.generic_visit(node)

    def _symbols(self) -> list[str]:
        symbol = ".".join([self.module, *self.scope])
        if self.module == _GENERATED_MODULE and len(self.scope) == 1:
            return [symbol, f"{_GENERATED_TARGET}.{self.scope[0]}"]
        return [symbol]


def scan_sdk(sdk_root: Path = SDK_ROOT) -> list[SdkCall]:
    """Return every literal route call in the SDK package, sorted for stable output."""
    calls: list[SdkCall] = []
    for source in sorted(sdk_root.rglob("*.py")):
        module = ".".join(source.relative_to(sdk_root.parent).with_suffix("").parts)
        tree = ast.parse(source.read_text(encoding="utf-8"))
        visitor = _Visitor(module, _Module(tree))
        visitor.visit(tree)
        calls.extend(visitor.calls)
    return sorted(calls, key=lambda c: (c.path, c.method, c.sdk_symbol, c.line))


if __name__ == "__main__":
    found = scan_sdk()
    print(f"{len(found)} route calls in {len({c.sdk_symbol for c in found})} SDK functions")
