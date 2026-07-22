"""Static source guards enforced across the whole CLI package.

These must always pass. They prevent a second Mammoth HTTP client, private SDK
access, and hardcoded secrets from ever entering the CLI source.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

CLI_PKG = Path(__file__).resolve().parent.parent.parent / "mammoth_cli"

FORBIDDEN_TRANSPORT = {"requests", "httpx", "aiohttp", "urllib3", "http.client"}
# Public SDK entry modules the CLI may import.
ALLOWED_SDK_ROOTS = {"mammoth"}


def _py_files() -> list[Path]:
    return sorted(CLI_PKG.rglob("*.py"))


def test_cli_never_implements_mammoth_http() -> None:
    offenders: list[str] = []
    for path in _py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in FORBIDDEN_TRANSPORT:
                        offenders.append(f"{path.name}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".")[0]
                if root in FORBIDDEN_TRANSPORT:
                    offenders.append(f"{path.name}: from {node.module}")
    assert not offenders, f"CLI must not import a transport client: {offenders}"


def test_cli_never_calls_private_sdk_members() -> None:
    offenders: list[str] = []
    for path in _py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            # Attribute access to a private member of an object.
            if (
                isinstance(node, ast.Attribute)
                and node.attr.startswith("_")
                and not node.attr.startswith("__")
            ):
                # Allow private attributes on `self` and on the CLI's own modules.
                if isinstance(node.value, ast.Name) and node.value.id == "self":
                    continue
                offenders.append(f"{path.name}:{node.lineno}: .{node.attr}")
            # `from mammoth._x import ...`
            if isinstance(node, ast.ImportFrom) and node.module:
                parts = node.module.split(".")
                if parts[0] == "mammoth" and any(p.startswith("_") for p in parts[1:]):
                    offenders.append(f"{path.name}: from {node.module}")
    assert not offenders, f"CLI must not touch private SDK members: {offenders[:20]}"


def test_no_hardcoded_secrets_in_source() -> None:
    pattern = re.compile(
        r"(api[_-]?secret|password|private[_-]?key)\s*=\s*['\"][^'\"]{6,}['\"]", re.I
    )
    offenders: list[str] = []
    for path in _py_files():
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line) and "getenv" not in line and "environ" not in line:
                offenders.append(f"{path.name}:{lineno}")
    assert not offenders, f"possible hardcoded secret: {offenders}"
