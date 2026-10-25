"""References and conditions between the steps of a run or task: JSON only, no code."""

from __future__ import annotations

from typing import Any

import pytest

from mammoth_cli.runtime.bindings import (
    BindingError,
    Unresolved,
    contains_unresolved,
    evaluate,
    lookup,
    resolve,
    split_path,
)

SCOPE: dict[str, Any] = {
    "steps": {
        "upload": {"data": {"dataset_id": 12, "views": [{"id": 3}, {"id": 4}], "name": "s"}},
        "empty": {"data": []},
    },
    "pending": ["later"],
}


def test_split_path_reads_keys_and_indexes() -> None:
    assert split_path("steps.a.data.items[0].id") == ["steps", "a", "data", "items", 0, "id"]


@pytest.mark.parametrize("bad", ["steps..a", "steps.a b", "steps.[x]"])
def test_split_path_refuses_malformed(bad: str) -> None:
    with pytest.raises(BindingError):
        split_path(bad)


def test_a_whole_reference_keeps_its_type() -> None:
    assert resolve("{{steps.upload.data.dataset_id}}", SCOPE) == 12
    assert resolve("{{ steps.upload.data.views[1].id }}", SCOPE) == 4


def test_an_inner_reference_is_written_as_text() -> None:
    assert resolve("dataset {{steps.upload.data.dataset_id}}", SCOPE) == "dataset 12"


def test_containers_resolve_recursively() -> None:
    value = {"ids": ["{{steps.upload.data.dataset_id}}", 1], "keep": True}
    assert resolve(value, SCOPE) == {"ids": [12, 1], "keep": True}


def test_a_missing_reference_names_its_path() -> None:
    with pytest.raises(BindingError) as caught:
        resolve("{{steps.nope.data}}", SCOPE)
    assert caught.value.path == "steps.nope.data"


def test_value_operators() -> None:
    data = "{{steps.upload.data}}"
    assert resolve({"$keys": data}, SCOPE) == ["dataset_id", "views", "name"]
    assert resolve({"$first": "{{steps.upload.data.views}}"}, SCOPE) == {"id": 3}
    assert resolve({"$first": "{{steps.empty.data}}"}, SCOPE) is None
    assert resolve({"$without": [[1, 2, 3], 2]}, SCOPE) == [1, 3]
    assert resolve({"$default": ["{{steps.nope.data}}", 5]}, SCOPE) == 5
    assert resolve({"$default": ["{{steps.upload.data.dataset_id}}", 5]}, SCOPE) == 12


def test_a_malformed_operator_is_refused() -> None:
    with pytest.raises(BindingError):
        resolve({"$first": "{{steps.upload.data}}"}, SCOPE)


def test_other_dollar_keys_are_data() -> None:
    schema = {"$schema": "draft-07", "$ref": "#/a", "n": "{{steps.upload.data.name}}"}
    assert resolve(schema, SCOPE) == {**schema, "n": "s"}
    # An operator key beside others is a mistake, not data (second review of #318).
    with pytest.raises(BindingError, match="only key"):
        resolve({"$first": "{{steps.empty.data}}", "extra": 1}, SCOPE)


@pytest.mark.parametrize("bare", ["steps.upload.data.ok", "yes", "x {{steps.upload.data.name}}"])
def test_a_bare_string_condition_is_refused(bare: str) -> None:
    with pytest.raises(BindingError, match="always true"):
        evaluate(bare, SCOPE)


def test_plan_mode_stands_in_for_pending_steps() -> None:
    value = resolve({"id": "{{steps.later.data.id}}"}, SCOPE, plan=True)
    assert value == {"id": Unresolved("steps.later.data.id")}
    assert contains_unresolved(value)
    assert str(value["id"]) == "<steps.later.data.id>"
    assert lookup(SCOPE, "steps.upload.data.dataset_id", plan=True) == 12


@pytest.mark.parametrize(
    ("condition", "expected"),
    [
        ("{{steps.upload.data.name}}", True),
        ({"eq": ["{{steps.upload.data.dataset_id}}", 12]}, True),
        ({"in": [4, [3, 4]]}, True),
        ({"not": {"eq": [1, 2]}}, True),
        ({"all": [{"eq": [1, 1]}, {"eq": [1, 2]}]}, False),
        ({"any": [{"eq": [1, 1]}, {"eq": [1, 2]}]}, True),
        ({"present": "{{steps.upload.data.name}}"}, True),
        ({"present": "{{steps.empty.data}}"}, False),
        ({"present": "{{steps.nope.data}}"}, False),
    ],
)
def test_conditions(condition: Any, expected: bool) -> None:
    assert evaluate(condition, SCOPE) is expected


def test_a_condition_on_a_pending_step_is_unknown_in_a_plan() -> None:
    assert evaluate({"eq": ["{{steps.later.data.x}}", 1]}, SCOPE, plan=True) is None
    assert evaluate({"all": [{"eq": [1, 2]}, "{{steps.later.data}}"]}, SCOPE, plan=True) is False


@pytest.mark.parametrize("bad", [{"exec": "x"}, {"eq": [1]}, {"in": [1, 2]}, 5, {"present": 1}])
def test_malformed_conditions_are_refused(bad: Any) -> None:
    with pytest.raises(BindingError):
        evaluate(bad, SCOPE)
