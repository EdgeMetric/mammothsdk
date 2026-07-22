#!/usr/bin/env python3
"""Generate the public SDK method inventory by introspection.

Scope (matches plan appendix 13): every public (non-underscore) method declared
directly on a class defined in ``mammoth/client.py``, ``mammoth/view.py``,
``mammoth/api/``, or ``mammoth/_mixins/``. Transformation mixin methods are
invoked publicly through ``mammoth.view.View``; they are recorded under their
implementation symbol.

Excluded: private names, dunder methods, members inherited from ``object`` or
third-party bases (Pydantic/dataclass utilities), and members not defined in the
class body of an in-scope class.

The output is deterministic and sorted by fully qualified symbol. A test asserts
the generated file matches live introspection so the manifest cannot drift.
"""

from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GENERATOR_VERSION = "1"


def _iter_in_scope_modules() -> list[str]:
    import mammoth._mixins as mixins_pkg
    import mammoth.api as api_pkg

    modules = ["mammoth.client", "mammoth.view"]
    for pkg in (api_pkg, mixins_pkg):
        for info in pkgutil.iter_modules(pkg.__path__):
            if info.name.startswith("__"):
                continue
            modules.append(f"{pkg.__name__}.{info.name}")
    return sorted(set(modules))


def _format_signature(func: Any) -> str:
    try:
        sig = inspect.signature(func)
    except (ValueError, TypeError):
        return "(...)"
    text = str(sig)
    # Normalise fully qualified annotation noise into short forms.
    return text


def collect() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for module_name in _iter_in_scope_modules():
        module = importlib.import_module(module_name)
        for cls_name, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != module_name:
                continue  # only classes defined in this module
            for attr_name, member in cls.__dict__.items():
                if attr_name.startswith("_"):
                    continue
                func = None
                kind = None
                if inspect.isfunction(member):
                    func = member
                    kind = "method"
                elif isinstance(member, staticmethod):
                    func = member.__func__
                    kind = "staticmethod"
                elif isinstance(member, classmethod):
                    func = member.__func__
                    kind = "classmethod"
                elif isinstance(member, property):
                    func = member.fget
                    kind = "property"
                else:
                    continue
                if func is None:
                    continue
                symbol = f"{module_name}.{cls_name}.{attr_name}"
                if symbol in seen:
                    continue
                seen.add(symbol)
                try:
                    line = inspect.getsourcelines(func)[1]
                except (OSError, TypeError):
                    line = 0
                records.append(
                    {
                        "sdk_symbol": symbol,
                        "kind": kind,
                        "signature": f"{attr_name}{_format_signature(func)}",
                        "source": f"{func.__module__.replace('.', '/')}.py:{line}",
                    }
                )
    records.sort(key=lambda record: record["sdk_symbol"])
    return records


def build_document() -> dict[str, Any]:
    records = collect()
    return {
        "generator_version": GENERATOR_VERSION,
        "scope": "public methods/properties on classes in client.py, view.py, api/, _mixins/",
        "method_count": len(records),
        "methods": records,
    }


def main() -> int:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    document = build_document()
    print(json.dumps({"method_count": document["method_count"]}, indent=2))
    out = Path(__file__).resolve().parent.parent / "spec" / "manifests" / "_sdk_introspection.json"
    out.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
