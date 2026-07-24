"""Unit tests for JSON-to-typed-argument coercion.

Exercises :func:`mammoth_cli.services.coerce.coerce_arguments` against real
bound SDK ``View`` methods and real SDK types, so the tests fail if coercion
ever crashes on or silently mangles a legitimate JSON-shaped argument.
"""

from __future__ import annotations

from mammoth.api.automations import AutomationsAPI
from mammoth.api.clientapps import ClientAppsAPI
from mammoth.api.external_keys import ExternalKeysAPI
from mammoth.api.projects import ProjectsAPI
from mammoth.condition import Condition
from mammoth.models.automations import (
    AutomationConditionMode,
    AutomationPatchItem,
    AutomationTaskSpec,
)
from mammoth.models.clientapps import PatchRequest
from mammoth.models.external_keys import ExternalKeyType, ModelConfigSpec
from mammoth.models.pipeline import SetValue, SortDirection
from mammoth.view import View

from mammoth_cli.services.coerce import coerce_arguments


def test_union_str_or_enum_keeps_non_enum_string_and_coerces_valid_direction() -> None:
    """A column literally named like text that isn't a direction stays a string.

    ``View.limit_rows`` types its ``order_by`` elements as ``str |
    SortDirection``. A column name such as "Sales" is not a valid
    ``SortDirection`` member and must be coerced through unchanged as a plain
    string, while a valid direction string ("ASC") must become the enum
    member -- not raise ``ValueError`` from a failed blind enum construction.
    """
    result = coerce_arguments(
        View.limit_rows,
        {"n": 10, "order_by": [["Sales", "ASC"]]},
    )

    column, direction = result["order_by"][0]
    assert column == "Sales"
    assert isinstance(column, str)
    assert direction is SortDirection.ASC


def test_dataclass_condition_field_is_compiled_not_left_as_raw_dict() -> None:
    """A nested ``SetValue.condition`` dict becomes a real compiled Condition.

    ``SetValue.condition`` is typed ``Condition | CompoundCondition |
    NotCondition | None``, a forward reference resolvable only via the SDK
    type namespace. Coercion must both resolve that annotation and route the
    dict spec through ``compile_condition`` rather than passing it through
    raw.
    """
    result = coerce_arguments(
        View.set_values,
        {
            "values": [
                {
                    "value": "High",
                    "condition": {"column": "Sales", "operator": "GTE", "value": 10000},
                }
            ]
        },
    )

    set_value = result["values"][0]
    assert isinstance(set_value, SetValue)
    assert isinstance(set_value.condition, Condition)
    assert set_value.condition.column == "Sales"
    assert set_value.condition.operator == "GTE"
    assert set_value.condition.value == 10000


def test_pydantic_list_field_becomes_models_for_automation_create() -> None:
    """``automation create`` task dicts must become ``AutomationTaskSpec`` models.

    ``AutomationsAPI.create`` types ``tasks`` as ``list[AutomationTaskSpec]``
    (pydantic v2) and ``condition_mode`` as the ``AutomationConditionMode``
    enum. The generic (non-View) command path must coerce JSON input into these
    types, or the SDK crashes on the raw dict. This is the Batch A HIGH fix.
    """
    result = coerce_arguments(
        AutomationsAPI.create,
        {
            "name": "n",
            "description": "d",
            "tasks": [{"task_type": "send_an_alert", "details": {}}],
            "condition_mode": "and",
        },
    )

    assert isinstance(result["tasks"][0], AutomationTaskSpec)
    assert result["condition_mode"] is AutomationConditionMode.AND


def test_pydantic_list_field_becomes_models_for_automation_update() -> None:
    """``automation update`` patch dicts must become ``AutomationPatchItem`` models."""
    result = coerce_arguments(
        AutomationsAPI.update,
        {"automation_id": 5, "patch": [{"op": "replace", "path": "status", "value": "active"}]},
    )

    assert isinstance(result["patch"][0], AutomationPatchItem)


def test_enum_and_pydantic_model_coerced_for_external_key_create() -> None:
    """``external-key create`` coerces the key-type enum and the settings model."""
    result = coerce_arguments(
        ExternalKeysAPI.create,
        {
            "key_type": "open_ai",
            "key_name": "k",
            "secure_key": "s",
            "model_settings": {"web_search": True},
        },
    )

    assert isinstance(result["key_type"], ExternalKeyType)
    assert isinstance(result["model_settings"], ModelConfigSpec)


def test_type_checking_only_pydantic_annotation_resolves_for_client_app_update() -> None:
    """``client-app update`` resolves a ``PatchRequest`` imported only under TYPE_CHECKING.

    ``ClientAppsAPI.update`` annotates ``patch_request`` with a model its module
    imports solely under ``TYPE_CHECKING``. Coercion must still resolve the name
    via the SDK-model namespace and build the model from JSON input.
    """
    result = coerce_arguments(
        ClientAppsAPI.update,
        {
            "client_key": "ck",
            "patch_request": {"patch": [{"op": "replace", "path": "/name", "value": "x"}]},
        },
    )

    assert isinstance(result["patch_request"], PatchRequest)


def test_plain_arguments_pass_through_unchanged() -> None:
    """A method with no coercible annotations leaves its arguments untouched."""
    result = coerce_arguments(ProjectsAPI.create, {"name": "p"})

    assert result["name"] == "p"
