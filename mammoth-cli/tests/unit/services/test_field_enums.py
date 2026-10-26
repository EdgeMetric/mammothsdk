"""Every fixed-vocabulary string field carries a schema ``enum`` and fails locally with the list."""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.commands.schema import get_schema, schema_entries
from mammoth_cli.errors.envelope import CliError
from mammoth_cli.runtime.strict import validate_input_fields
from mammoth_cli.services.field_enums import (
    ENUM_LIKE_FIELD_NAMES,
    FIELD_ENUMS,
    OPEN_VOCABULARY_ALLOWLIST,
    match_choice,
)


def _string_leaves(node: Any, path: tuple[str, ...]) -> list[tuple[tuple[str, ...], dict]]:
    found: list[tuple[tuple[str, ...], dict]] = []
    if not isinstance(node, dict):
        return found
    for name, child in (node.get("properties") or {}).items():
        found.extend(_string_leaves(child, (*path, name)))
    for key in ("anyOf", "oneOf"):
        for member in node.get(key) or []:
            found.extend(_string_leaves(member, path))
    if "items" in node:
        found.extend(_string_leaves(node["items"], (*path, "[]")))
    if path and node.get("type") == "string":
        found.append((path, node))
    return found


def _top_level_enums() -> list[tuple[str, str, list[Any]]]:
    rows: list[tuple[str, str, list[Any]]] = []
    for entry in schema_entries():
        command_id = entry["command_id"]
        schema = get_schema(command_id)
        assert schema is not None
        properties = dict(schema["input_schema"] or {}).get("properties", {})
        for name, prop in properties.items():
            members = [prop, *(prop.get("anyOf") or []), *(prop.get("oneOf") or [])]
            for member in members:
                values = member.get("enum") if isinstance(member, dict) else None
                if values and all(isinstance(v, str) for v in values):
                    rows.append((command_id, name, list(values)))
                    break
    return rows


def test_every_enum_like_string_field_has_an_enum() -> None:
    missing: list[str] = []
    for entry in schema_entries():
        command_id = entry["command_id"]
        schema = get_schema(command_id)
        assert schema is not None
        for path, leaf in _string_leaves(dict(schema["input_schema"] or {}), ()):
            name = path[-1]
            if name not in ENUM_LIKE_FIELD_NAMES or "enum" in leaf or "const" in leaf:
                continue
            if (command_id, name) in OPEN_VOCABULARY_ALLOWLIST:
                continue
            missing.append(f"{command_id}:{'.'.join(path)}")
    assert not missing, "string fields that look like fixed vocabularies lack an enum: " + str(
        missing
    )


@pytest.mark.parametrize(
    ("command_id", "field"),
    [(cid, f) for cid, fields in FIELD_ENUMS.items() for f in fields],
)
def test_registered_field_shows_its_enum_in_schema_get(command_id: str, field: str) -> None:
    schema = get_schema(command_id)
    assert schema is not None
    prop = dict(schema["input_schema"])["properties"][field]
    members = [prop, *(prop.get("anyOf") or [])]
    assert any(m.get("enum") == list(FIELD_ENUMS[command_id][field]) for m in members), prop


@pytest.mark.parametrize("row", _top_level_enums(), ids=lambda r: f"{r[0]}:{r[1]}")
def test_enum_field_fails_locally_with_accepted_and_normalises_case(
    row: tuple[str, str, list[Any]],
) -> None:
    command_id, field, values = row
    with pytest.raises(CliError) as caught:
        validate_input_fields(command_id, {field: "definitely-not-a-value-xyz"})
    details = caught.value.details or {}
    assert details.get("accepted") == values
    assert "did_you_mean" in details
    for value in values[:1]:
        document = {field: value.swapcase() if value.swapcase() != value else value}
        validate_input_fields(command_id, document)
        assert document[field] == value


def test_did_you_mean_names_the_closest_value() -> None:
    with pytest.raises(CliError) as caught:
        validate_input_fields("annotation.update", {"status": "resolvd"})
    assert caught.value.details["did_you_mean"] == "resolved"
    assert "Did you mean 'resolved'" in caught.value.message


def test_registered_value_is_normalised_in_place() -> None:
    document = {"param_type": "date"}
    validate_input_fields("parameter.create", document)
    assert document["param_type"] == "DATE"


def test_match_choice_ignores_case_spaces_and_hyphens() -> None:
    assert match_choice("Data Quality", ("stats", "data_quality")) == ("data_quality", None)
    assert match_choice("zzz", ("stats",)) == (None, None)


@pytest.mark.parametrize(
    "command_id", ["view.conditional-format.create", "view.conditional-format.replace"]
)
def test_a_guessed_highlight_colour_is_refused_before_the_request_with_the_swatches(
    command_id: str,
) -> None:
    """P5 of the 10-26 speed pass: 5 of 6 agent runs sent "yellow" and learned the swatches
    from the backend's 400, costing a rejected write and a ``schema get`` round."""
    schema = get_schema(command_id)
    assert schema is not None
    prop = dict(schema["input_schema"])["properties"]["color"]
    listed = [m.get("enum") for m in [prop, *(prop.get("anyOf") or [])]]
    assert any(values and "amber" in values and "yellow" not in values for values in listed)

    with pytest.raises(CliError) as caught:
        validate_input_fields(command_id, {"color": "yellow"})
    assert "amber" in (caught.value.details or {})["accepted"]

    document = {"color": "Amber"}
    validate_input_fields(command_id, document)
    assert document["color"] == "amber"
