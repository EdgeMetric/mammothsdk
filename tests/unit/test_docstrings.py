"""Permanent docstring validation tests for ALL public SDK functions.

Ensures every public method, enum, dataclass, and exception has a docstring,
and that documented Args match actual function signatures.
"""

from __future__ import annotations

import importlib
import inspect
import re
from typing import Any

import pytest

from mammoth.client import MammothClient, ViewsResource
from mammoth.condition import CompoundCondition, Condition, NotCondition
from mammoth.view import View, ViewExport

# ── Helpers ──────────────────────────────────────────────────────


def _get_public_methods(cls: type) -> list[tuple[str, Any]]:
    """Return (name, method) for all public methods of a class."""
    methods = []
    for name in sorted(dir(cls)):
        if name.startswith("_"):
            continue
        try:
            attr = getattr(cls, name)
        except AttributeError:
            continue
        if callable(attr):
            methods.append((name, attr))
    return methods


def _get_sig_params(func: Any) -> set[str]:
    """Get all param names (excluding self/cls) from a function signature."""
    try:
        sig = inspect.signature(func)
    except (ValueError, TypeError):
        return set()
    return {
        name
        for name, p in sig.parameters.items()
        if name not in ("self", "cls") and p.kind != p.VAR_KEYWORD
    }


def _parse_docstring_args(docstring: str) -> set[str]:
    """Extract parameter names from a Google-style Args: section."""
    args: list[str] = []
    in_args = False
    for line in docstring.splitlines():
        stripped = line.strip()
        if stripped.startswith("Args:"):
            in_args = True
            continue
        if in_args:
            if stripped in (
                "Returns:",
                "Raises:",
                "Example::",
                "Examples::",
                "Note:",
                "Yields:",
                "Attributes:",
            ):
                break
            # Also break on single-word section headers
            if (
                stripped
                and stripped.endswith(":")
                and " " not in stripped.rstrip(":")
                and not stripped.startswith("*")
            ):
                break
            m = re.match(r"^(\w+)\s*(?:\(.*?\))?\s*:", stripped)
            if m and not stripped.startswith("**"):
                args.append(m.group(1))
    return set(args)


# ── Core class method docstrings ─────────────────────────────────


CORE_CLASSES = [
    MammothClient,
    ViewsResource,
    View,
    ViewExport,
    Condition,
    CompoundCondition,
    NotCondition,
]


@pytest.mark.parametrize(
    "cls",
    CORE_CLASSES,
    ids=[c.__name__ for c in CORE_CLASSES],
)
class TestCoreClassDocstrings:
    """Every public method on core classes must have a docstring."""

    def test_class_has_docstring(self, cls: type):
        assert inspect.getdoc(cls), f"{cls.__name__} missing class docstring"

    def test_all_public_methods_have_docstrings(self, cls: type):
        for name, method in _get_public_methods(cls):
            doc = inspect.getdoc(method)
            assert doc, f"{cls.__name__}.{name}() missing docstring"


# ── Mixin transformation method docstrings ───────────────────────


MIXIN_CLASSES: list[type] = []
MIXIN_IDS: list[str] = []

from mammoth._mixins import (  # noqa: E402
    AdvancedOpsMixin,
    AggregateOpsMixin,
    ColumnOpsMixin,
    DateOpsMixin,
    FilterOpsMixin,
    MathOpsMixin,
    RowOpsMixin,
    TextOpsMixin,
)

for _mixin in [
    ColumnOpsMixin,
    FilterOpsMixin,
    MathOpsMixin,
    TextOpsMixin,
    DateOpsMixin,
    AggregateOpsMixin,
    RowOpsMixin,
    AdvancedOpsMixin,
]:
    MIXIN_CLASSES.append(_mixin)
    MIXIN_IDS.append(_mixin.__name__)


@pytest.mark.parametrize("cls", MIXIN_CLASSES, ids=MIXIN_IDS)
class TestMixinDocstrings:
    """Every transformation method in every mixin must have a docstring."""

    def test_all_methods_have_docstrings(self, cls: type):
        for name, method in _get_public_methods(cls):
            doc = inspect.getdoc(method)
            assert doc, f"{cls.__name__}.{name}() missing docstring"


# ── Docstring Args match function signature ──────────────────────


# Collect all (cls, method_name, method) triples for transformation methods
_SIG_CHECK_ITEMS: list[tuple[str, str, Any]] = []
for _cls in [View, ViewExport, *MIXIN_CLASSES]:
    for _name, _method in _get_public_methods(_cls):
        _SIG_CHECK_ITEMS.append((_cls.__name__, _name, _method))


@pytest.mark.parametrize(
    "cls_name, method_name, method",
    _SIG_CHECK_ITEMS,
    ids=[f"{c}.{m}" for c, m, _ in _SIG_CHECK_ITEMS],
)
class TestDocstringArgsMatchSignature:
    """Documented Args must match actual function params for transform methods."""

    def test_no_stale_documented_params(self, cls_name: str, method_name: str, method: Any):
        """No documented param should be absent from the actual signature."""
        doc = inspect.getdoc(method)
        if not doc or "Args:" not in doc:
            pytest.skip("No Args section")
        sig_params = _get_sig_params(method)
        doc_args = _parse_docstring_args(doc)
        for arg in doc_args:
            assert arg in sig_params, (
                f"{cls_name}.{method_name}() documents param '{arg}' "
                f"but signature only has: {sorted(sig_params)}"
            )

    def test_required_params_documented(self, cls_name: str, method_name: str, method: Any):
        """Every required param (no default) should appear in the Args section."""
        doc = inspect.getdoc(method)
        if not doc or "Args:" not in doc:
            pytest.skip("No Args section")
        try:
            sig = inspect.signature(method)
        except (ValueError, TypeError):
            pytest.skip("Cannot inspect signature")
        doc_args = _parse_docstring_args(doc)
        for pname, param in sig.parameters.items():
            if pname in ("self", "cls"):
                continue
            if param.kind in (param.VAR_KEYWORD, param.VAR_POSITIONAL):
                continue
            if param.default is inspect.Parameter.empty:
                assert pname in doc_args, (
                    f"{cls_name}.{method_name}() has required param '{pname}' "
                    f"not documented in Args section"
                )


# ── Enum docstrings ──────────────────────────────────────────────


from mammoth.models.pipeline import (  # noqa: E402
    AggregateFunction,
    ColumnType,
    DateComponent,
    DateDiffUnit,
    DraftCommand,
    ExportFileType,
    FillDirection,
    FilterType,
    JoinType,
    JsonOpType,
    JsonType,
    MathOperator,
    Operator,
    ProviderType,
    SortDirection,
    SubstringDirection,
    TaskType,
    TextCase,
    ValueType,
    WindowFunction,
    WindowRange,
)

ALL_ENUMS = [
    Operator,
    ColumnType,
    ValueType,
    JoinType,
    TextCase,
    DateComponent,
    DateDiffUnit,
    WindowFunction,
    WindowRange,
    FillDirection,
    AggregateFunction,
    ProviderType,
    FilterType,
    SortDirection,
    MathOperator,
    SubstringDirection,
    JsonType,
    JsonOpType,
    ExportFileType,
    TaskType,
    DraftCommand,
]


@pytest.mark.parametrize("enum_cls", ALL_ENUMS, ids=[e.__name__ for e in ALL_ENUMS])
def test_enum_has_docstring(enum_cls: type):
    """Every public enum must have a docstring."""
    assert inspect.getdoc(enum_cls), f"{enum_cls.__name__} missing docstring"


# ── Dataclass docstrings ─────────────────────────────────────────


from mammoth.models.pipeline import (  # noqa: E402
    AggregationSpec,
    BulkReplaceMapping,
    ConversionSpec,
    CopySpec,
    CrosstabSpec,
    DateDelta,
    JoinKeySpec,
    JoinSelectSpec,
    JsonExtractionSpec,
    SetValue,
    SplitColumnSpec,
)

ALL_DATACLASSES = [
    SetValue,
    SplitColumnSpec,
    BulkReplaceMapping,
    DateDelta,
    CopySpec,
    ConversionSpec,
    AggregationSpec,
    JoinKeySpec,
    JoinSelectSpec,
    JsonExtractionSpec,
    CrosstabSpec,
]


@pytest.mark.parametrize("dc_cls", ALL_DATACLASSES, ids=[d.__name__ for d in ALL_DATACLASSES])
def test_dataclass_has_docstring(dc_cls: type):
    """Every public dataclass must have a docstring."""
    assert inspect.getdoc(dc_cls), f"{dc_cls.__name__} missing docstring"


# ── Exception docstrings ─────────────────────────────────────────


from mammoth.exceptions import (  # noqa: E402
    MammothAPIError,
    MammothAuthError,
    MammothColumnError,
    MammothError,
    MammothJobFailedError,
    MammothJobTimeoutError,
    MammothTransformError,
)

ALL_EXCEPTIONS = [
    MammothError,
    MammothAPIError,
    MammothAuthError,
    MammothJobTimeoutError,
    MammothJobFailedError,
    MammothTransformError,
    MammothColumnError,
]


@pytest.mark.parametrize("exc_cls", ALL_EXCEPTIONS, ids=[e.__name__ for e in ALL_EXCEPTIONS])
def test_exception_has_docstring(exc_cls: type):
    """Every exception class must have a docstring."""
    assert inspect.getdoc(exc_cls), f"{exc_cls.__name__} missing docstring"


# ── API sub-client docstrings ────────────────────────────────────


_API_MODULES = [
    "mammoth.api.activity_logs",
    "mammoth.api.addons",
    "mammoth.api.ai",
    "mammoth.api.automations",
    "mammoth.api.batches",
    "mammoth.api.browse",
    "mammoth.api.clientapps",
    "mammoth.api.connectors",
    "mammoth.api.dashboards",
    "mammoth.api.datasets",
    "mammoth.api.dataviews",
    "mammoth.api.exports",
    "mammoth.api.external_keys",
    "mammoth.api.files",
    "mammoth.api.folders",
    "mammoth.api.jobs",
    "mammoth.api.pipeline",
    "mammoth.api.projects",
    "mammoth.api.reports",
    "mammoth.api.schedules",
    "mammoth.api.user_profile",
    "mammoth.api.webhooks",
    "mammoth.api.workspace",
]

_API_CLASSES: list[tuple[str, type]] = []
for _mod_name in _API_MODULES:
    _mod = importlib.import_module(_mod_name)
    for _attr_name in dir(_mod):
        _obj = getattr(_mod, _attr_name)
        if isinstance(_obj, type) and _attr_name.endswith("API"):
            _API_CLASSES.append((_attr_name, _obj))


@pytest.mark.parametrize("cls_name, cls", _API_CLASSES, ids=[name for name, _ in _API_CLASSES])
class TestAPISubClientDocstrings:
    """Every public method on every API sub-client must have a docstring."""

    def test_all_methods_have_docstrings(self, cls_name: str, cls: type):
        for name, method in _get_public_methods(cls):
            doc = inspect.getdoc(method)
            assert doc, f"{cls_name}.{name}() missing docstring"


# ── __init__.py exports everything listed in __all__ ─────────────


def test_all_exports_importable():
    """Every item in mammoth.__all__ must be importable."""
    import mammoth

    for name in mammoth.__all__:
        obj = getattr(mammoth, name, None)
        assert obj is not None, f"mammoth.__all__ lists '{name}' but it's not importable"


def test_version_is_string():
    """mammoth.__version__ must be a semver string."""
    import mammoth

    assert isinstance(mammoth.__version__, str)
    parts = mammoth.__version__.split(".")
    assert len(parts) >= 2, f"Version '{mammoth.__version__}' not semver"
    for p in parts:
        assert p.isdigit(), f"Version part '{p}' is not numeric"
