"""Contract tests for generated dashboard request-model constraints.

Two review blockers are guarded here:

* **Blocker A** — the generator must translate every OpenAPI validation
  keyword (``minimum``/``maximum``/``exclusiveMinimum``/``exclusiveMaximum``,
  ``minLength``/``maxLength``, ``minItems``/``maxItems``, ``pattern``,
  ``multipleOf``) into a ``pydantic`` ``Field`` constraint so invalid request
  payloads are rejected client-side. Covered by the three named specs plus a
  data-driven boundary sweep over every reachable *request* schema that
  carries a constraint.
* **Blocker B** — ``DashboardAuth`` is reachable as both a request field and a
  response field. The request variant must stay strict (``extra="forbid"``)
  while a separate response variant must tolerate additive server fields.
* **Blocker #4** — the generator must also honour the JSON-Schema ``format``
  keyword. Every string field with ``format: uuid`` in a reachable *request*
  schema must carry the anchored UUID ``pattern`` in the generated strict
  model (so a malformed UUID is rejected), while the field still serialises as
  a plain ``str``. Covered by a spec-derived audit plus explicit
  valid/malformed value tests on ``WidgetDataParams``.

The constraint inventory and baseline payloads are derived from the pinned
OpenAPI snapshot (never the network), mirroring how the other contract tests
enumerate schemas, so this suite fails *before* the generator is fixed and is
maintainable as the snapshot evolves.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

import mammoth.models.dashboard_generated as models
import pytest
from pydantic import BaseModel, ValidationError

CLI_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = CLI_ROOT / "scripts"

VALID_UUID = "550e8400-e29b-41d4-a716-446655440000"

CONSTRAINT_KEYS = {
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
    "pattern",
    "multipleOf",
}


def _generator() -> Any:
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    import gen_dashboard_v3_sdk

    return gen_dashboard_v3_sdk


def _document() -> dict[str, Any]:
    import json

    return json.loads(_generator().SNAPSHOT.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Spec-driven value construction (independent of the generated models, so the
# suite enumerates the right fields even before constraints are emitted).
# --------------------------------------------------------------------------- #


def _pick_variant(schema: dict[str, Any]) -> dict[str, Any]:
    """Collapse a ``oneOf``/``anyOf`` to its first non-null concrete variant."""
    variants = schema.get("oneOf") or schema.get("anyOf")
    if isinstance(variants, list):
        for variant in variants:
            if isinstance(variant, dict) and variant.get("type") != "null":
                merged = dict(variant)
                # carry sibling constraints (e.g. maxLength on the wrapper)
                for key in CONSTRAINT_KEYS:
                    if key in schema and key not in merged:
                        merged[key] = schema[key]
                return merged
    return schema


def _scalar_type(schema: dict[str, Any]) -> str | None:
    t = schema.get("type")
    if isinstance(t, list):
        for item in t:
            if item != "null":
                return str(item)
        return None
    return str(t) if t is not None else None


def _valid_value(schema: dict[str, Any], comps: dict[str, Any]) -> Any:
    """Produce a value that satisfies ``schema`` (and any constraints on it)."""
    schema = _pick_variant(schema)
    ref = schema.get("$ref")
    if ref:
        return _minimal_valid(str(ref).rsplit("/", 1)[-1], comps)
    if "enum" in schema:
        return schema["enum"][0]
    kind = _scalar_type(schema)
    if kind == "string":
        if schema.get("format") == "uuid" and "pattern" not in schema:
            return VALID_UUID
        length = schema.get("minLength", 1) or 1
        if "maxLength" in schema:
            length = min(length, schema["maxLength"])
        return "x" * max(int(length), 0)
    if kind in {"integer", "number"}:
        if "minimum" in schema:
            value: float = schema["minimum"]
        elif "exclusiveMinimum" in schema:
            value = schema["exclusiveMinimum"] + 1
        else:
            value = 1
        if "maximum" in schema:
            value = min(value, schema["maximum"])
        return int(value) if kind == "integer" else float(value)
    if kind == "boolean":
        return True
    if kind == "array":
        count = int(schema.get("minItems", 0) or 0)
        items = schema.get("items") if isinstance(schema.get("items"), dict) else {}
        return [_valid_value(items, comps) for _ in range(count)]
    if kind == "object" or "properties" in schema:
        return {}
    return None


def _minimal_valid(name: str, comps: dict[str, Any]) -> dict[str, Any]:
    """Build the minimal valid payload for component ``name`` (required fields)."""
    schema = comps[name]
    required = set(schema.get("required", []))
    props = schema.get("properties") or {}
    return {field: _valid_value(fs, comps) for field, fs in props.items() if field in required}


def _constrained_request_components() -> list[str]:
    gen = _generator()
    doc = _document()
    comps = doc["components"]["schemas"]
    request_reachable = gen._closure(doc, gen._request_seeds(doc))
    names = []
    for name in sorted(request_reachable):
        props = comps[name].get("properties") or {}
        if any(isinstance(fs, dict) and (set(fs) & CONSTRAINT_KEYS) for fs in props.values()):
            names.append(name)
    return names


def _boundary_cases() -> list[Any]:
    """Yield ``(model, field, label, payload, expect_valid)`` tuples.

    For every constrained field of every reachable request component: the
    boundary value must validate; a value one step below the lower bound must
    fail; and, where an upper bound exists, a value one step above it must fail.
    """
    doc = _document()
    comps = doc["components"]["schemas"]
    cases: list[Any] = []
    for name in _constrained_request_components():
        model = getattr(models, name)
        schema = comps[name]
        props = schema.get("properties") or {}
        base = _minimal_valid(name, comps)
        for field, raw in props.items():
            fs = _pick_variant(raw) if isinstance(raw, dict) else {}
            constraints = {k: fs[k] for k in CONSTRAINT_KEYS if k in fs}
            if not constraints:
                continue
            variants = _field_variants(fs, constraints, comps)
            for label, value, expect_valid in variants:
                payload = copy.deepcopy(base)
                payload[field] = value
                cases.append(
                    pytest.param(
                        model,
                        field,
                        payload,
                        expect_valid,
                        id=f"{name}.{field}.{label}",
                    )
                )
    return cases


def _field_variants(
    fs: dict[str, Any], constraints: dict[str, Any], comps: dict[str, Any]
) -> list[tuple[str, Any, bool]]:
    """Return ``(label, value, expect_valid)`` triples for one constrained field."""
    out: list[tuple[str, Any, bool]] = []
    kind = _scalar_type(fs)

    # Boundary value that must validate.
    out.append(("boundary", _valid_value(fs, comps), True))

    if kind == "string":
        if constraints.get("minLength", 0) >= 1:
            out.append(("below_min_length", "x" * (constraints["minLength"] - 1), False))
        if "maxLength" in constraints:
            out.append(("above_max_length", "x" * (constraints["maxLength"] + 1), False))
    elif kind in {"integer", "number"}:
        cast = int if kind == "integer" else float
        if "minimum" in constraints:
            out.append(("below_minimum", cast(constraints["minimum"] - 1), False))
        if "exclusiveMinimum" in constraints:
            out.append(("at_exclusive_minimum", cast(constraints["exclusiveMinimum"]), False))
        if "maximum" in constraints:
            out.append(("above_maximum", cast(constraints["maximum"] + 1), False))
        if "exclusiveMaximum" in constraints:
            out.append(("at_exclusive_maximum", cast(constraints["exclusiveMaximum"]), False))
    elif kind == "array":
        items = fs.get("items") if isinstance(fs.get("items"), dict) else {}
        item = _valid_value(items, comps)
        if constraints.get("minItems", 0) >= 1:
            out.append(("below_min_items", [item] * (constraints["minItems"] - 1), False))
        if "maxItems" in constraints:
            out.append(("above_max_items", [item] * (constraints["maxItems"] + 1), False))
    return out


BOUNDARY_CASES = _boundary_cases()


# --------------------------------------------------------------------------- #
# Blocker A: named specs
# --------------------------------------------------------------------------- #


def test_generate_dashboard_v3_spec_rejects_empty_intent_and_zero_dataview() -> None:
    with pytest.raises(ValidationError):
        models.GenerateDashboardV3Spec.model_validate({"params": {"dataview_id": 0, "intent": ""}})


def test_ask_spec_rejects_empty_question() -> None:
    with pytest.raises(ValidationError):
        models.AskSpec.model_validate({"params": {"question": ""}})


def test_bulk_widget_data_spec_rejects_empty_widgets() -> None:
    with pytest.raises(ValidationError):
        models.BulkWidgetDataSpec.model_validate({"params": {"widgets": []}})


def test_named_specs_accept_valid_boundary_payloads() -> None:
    """The valid boundary of each named spec must still validate."""
    models.GenerateDashboardV3Spec.model_validate({"params": {"dataview_id": 1, "intent": "x"}})
    models.AskSpec.model_validate({"params": {"question": "x"}})
    models.BulkWidgetDataSpec.model_validate(
        {"params": {"widgets": [{"widget_id": VALID_UUID}]}}
    )


# --------------------------------------------------------------------------- #
# Blocker A: data-driven boundary sweep over the reachable request closure
# --------------------------------------------------------------------------- #


def test_constrained_request_closure_is_nonempty() -> None:
    assert _constrained_request_components(), "expected constrained request schemas"
    assert BOUNDARY_CASES, "expected generated boundary cases"


@pytest.mark.parametrize(("model", "field", "payload", "expect_valid"), BOUNDARY_CASES)
def test_request_field_boundaries(
    model: type[BaseModel], field: str, payload: dict[str, Any], expect_valid: bool
) -> None:
    if expect_valid:
        model.model_validate(payload)
    else:
        with pytest.raises(ValidationError):
            model.model_validate(payload)


# --------------------------------------------------------------------------- #
# Blocker #4: JSON-Schema ``format: uuid`` -> anchored pattern on strict models
# --------------------------------------------------------------------------- #


def _uuid_request_fields() -> list[Any]:
    """Yield ``(model_name, field)`` for every ``format: uuid`` string field.

    Enumerated from the pinned OpenAPI over the reachable *request* closure,
    unwrapping ``oneOf``/``anyOf`` exactly as the generator does. Only fields
    without an explicit ``pattern`` are asserted to carry the format-derived
    UUID pattern (an explicit spec ``pattern`` would win instead).
    """
    gen = _generator()
    doc = _document()
    comps = doc["components"]["schemas"]
    request_reachable = gen._closure(doc, gen._request_seeds(doc))
    cases: list[Any] = []
    for name in sorted(request_reachable):
        props = comps[name].get("properties") or {}
        for field, raw in props.items():
            if not isinstance(raw, dict):
                continue
            fs = _pick_variant(raw)
            if fs.get("format") != "uuid":
                continue
            if fs.get("type") != "string" or "pattern" in fs:
                continue
            cases.append(pytest.param(name, field, id=f"{name}.{field}"))
    return cases


UUID_REQUEST_FIELDS = _uuid_request_fields()


def test_uuid_request_fields_present() -> None:
    """The audit must actually enumerate at least one ``format: uuid`` field."""
    assert UUID_REQUEST_FIELDS, "expected at least one format:uuid request field"


@pytest.mark.parametrize(("model_name", "field"), UUID_REQUEST_FIELDS)
def test_uuid_format_emits_anchored_pattern(model_name: str, field: str) -> None:
    """Every ``format: uuid`` request field carries the anchored UUID pattern."""
    model = getattr(models, model_name)
    prop = model.model_json_schema()["properties"][field]
    assert prop.get("pattern") == _generator()._UUID_PATTERN
    # The field must remain a plain string type (no UUID object / $ref coercion).
    assert prop.get("type") == "string"


def test_widget_data_params_rejects_malformed_uuid() -> None:
    with pytest.raises(ValidationError):
        models.WidgetDataParams.model_validate({"widget_id": "not-a-uuid"})


def test_widget_data_params_accepts_valid_uuid_and_dumps_as_string() -> None:
    valid = "550e8400-e29b-41d4-a716-446655440000"
    obj = models.WidgetDataParams.model_validate({"widget_id": valid})
    dumped = obj.model_dump(mode="json")
    assert dumped["widget_id"] == valid
    assert isinstance(dumped["widget_id"], str)


# --------------------------------------------------------------------------- #
# Blocker B: DashboardAuth request/response split
# --------------------------------------------------------------------------- #


def test_dashboard_auth_request_variant_rejects_additive_field() -> None:
    with pytest.raises(ValidationError):
        models.DashboardAuth.model_validate({"type_of_auth": "public", "server_added_field": "x"})


def test_dashboard_auth_response_variant_accepts_additive_field() -> None:
    assert hasattr(models, "DashboardAuthResponse"), "response variant must be generated"
    obj = models.DashboardAuthResponse.model_validate(
        {"type_of_auth": "public", "server_added_field": "x"}
    )
    assert obj.type_of_auth == "public"


def test_response_container_uses_lenient_dashboard_auth_variant() -> None:
    """A response schema's ``share`` field must reference the lenient variant."""
    annotation = models.V3DashboardMetaType.model_fields["share"].annotation
    assert models.DashboardAuthResponse in getattr(annotation, "__args__", (annotation,))


def test_request_container_uses_strict_dashboard_auth_variant() -> None:
    """A request schema's ``auth`` field must reference the strict variant."""
    annotation = models.DashboardShareParams.model_fields["auth"].annotation
    assert models.DashboardAuth in getattr(annotation, "__args__", (annotation,))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
