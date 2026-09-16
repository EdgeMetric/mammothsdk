"""Independent M3 resource-scope and display-name resolution checks.

The HTTP adapter in ``tests.conftest`` is only a transport double.  Metadata,
endpoint scope, and task payload assertions in this file are authored here,
independently of the resolver implementation, so a resolver that probes the
wrong parent or mutates before validation fails these tests.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from mammoth_cli.errors.envelope import CliError

PROJECT_ID = 180
LOCAL_DATASET = 55
FOREIGN_DATASET = 77
LOCAL_VIEW = 1039
FOREIGN_VIEW = 2050

ServiceFactory = Callable[..., Any]


def _metadata(view_id: int, columns: list[dict[str, str]]) -> dict[str, Any]:
    """Build a static metadata response used as the independent oracle."""
    return {"id": view_id, "name": f"view-{view_id}", "metadata": columns}


def _column(display: str, internal: str, column_type: str = "TEXT") -> dict[str, str]:
    return {"display_name": display, "internal_name": internal, "type": column_type}


def _configure(
    api: Any,
    *,
    local: list[dict[str, str]],
    foreign: list[dict[str, str]] | None = None,
) -> None:
    """Register exact-parent metadata and successful pipeline responses."""
    api.on(
        "GET",
        rf"/datasets/{LOCAL_DATASET}/dataviews/{LOCAL_VIEW}$",
        body=_metadata(LOCAL_VIEW, local),
    )
    if foreign is not None:
        api.on(
            "GET",
            rf"/datasets/{FOREIGN_DATASET}/dataviews/{FOREIGN_VIEW}$",
            body=_metadata(FOREIGN_VIEW, foreign),
        )
    api.on("POST", r"/pipeline/tasks$", body={})
    api.on("GET", r"/pipeline$", body={"state": "ready"})


def _posts(api: Any) -> list[Any]:
    return [request for request in api.requests if request.method == "POST"]


def _paths(api: Any) -> list[str]:
    return [request.path for request in api.requests]


def _has_path(api: Any, fragment: str) -> bool:
    """Match endpoint fragments while tolerating the configured API prefix."""
    return any(fragment in path for path in _paths(api))


def test_math_uses_exact_parent_and_condition_display_names(
    real_service: ServiceFactory,
) -> None:
    service, api = real_service(project_id=PROJECT_ID)
    _configure(
        api,
        local=[
            _column('Prix “brut”', "column_price", "NUMERIC"),
            _column("Qty / 値", "column_qty", "NUMERIC"),
        ],
    )

    service.call_view(
        LOCAL_VIEW,
        "math",
        dataset_id=LOCAL_DATASET,
        expression='Prix “brut” * Qty / 値',
        new_column="Total réservé",
        condition={"column": 'Prix “brut”', "operator": "GTE", "value": 1},
    )

    assert _has_path(api, f"/datasets/{LOCAL_DATASET}/dataviews/{LOCAL_VIEW}")
    assert not _has_path(api, f"/datasets/999/dataviews/{LOCAL_VIEW}")
    assert len(_posts(api)) == 1
    payload = _posts(api)[0].json_body["MATH"]
    assert [part["VALUE"] for part in payload["EXPRESSION"] if part["TYPE"] == "COLUMN"] == [
        "column_price",
        "column_qty",
    ]
    assert "column_price" in _posts(api)[0].json_body["CONDITION"]


def test_internal_local_column_id_is_rejected_before_post(real_service: ServiceFactory) -> None:
    service, api = real_service(project_id=PROJECT_ID)
    _configure(api, local=[_column("Price", "column_price", "NUMERIC")])

    with pytest.raises(CliError) as excinfo:
        service.call_view(
            LOCAL_VIEW,
            "math",
            dataset_id=LOCAL_DATASET,
            expression="column_price * 2",
            new_column="Total",
        )

    assert excinfo.value.code == "internal_column_name"
    assert _posts(api) == []


def test_unknown_and_ambiguous_local_names_are_zero_post(real_service: ServiceFactory) -> None:
    service, api = real_service(project_id=PROJECT_ID)
    _configure(
        api,
        local=[
            _column("Price", "column_price", "NUMERIC"),
            _column("Duplicate", "column_a"),
            _column("Duplicate", "column_b"),
        ],
    )

    with pytest.raises(CliError) as unknown:
        service.call_view(
            LOCAL_VIEW,
            "filter_rows",
            dataset_id=LOCAL_DATASET,
            condition={"column": "Missing", "operator": "EQ", "value": 1},
        )
    assert unknown.value.code == "unknown_column"
    assert "Price" in (unknown.value.details or {}).get("available", [])
    assert _posts(api) == []

    # A fresh service gives the ambiguous metadata its own independent GET;
    # no request from the first failed operation can affect this assertion.
    service2, api2 = real_service(project_id=PROJECT_ID)
    _configure(
        api2,
        local=[_column("Duplicate", "column_a"), _column("Duplicate", "column_b")],
    )
    with pytest.raises(CliError) as ambiguous:
        service2.call_view(
            LOCAL_VIEW,
            "math",
            dataset_id=LOCAL_DATASET,
            expression="Duplicate * 2",
            new_column="Total",
        )
    assert ambiguous.value.code == "unknown_column"
    assert ambiguous.value.details["available"] == []
    assert _posts(api2) == []


def test_three_duplicate_names_reject_math_condition_and_foreign_refs_before_post(
    real_service: ServiceFactory,
) -> None:
    """A third duplicate must not become a new arbitrary resolver winner."""
    service, api = real_service(project_id=PROJECT_ID)
    _configure(
        api,
        local=[
            _column("Amount", "local_amount_1", "NUMERIC"),
            _column("Amount", "local_amount_2", "NUMERIC"),
            _column("Amount", "local_amount_3", "NUMERIC"),
        ],
        foreign=[
            _column("Amount", "foreign_amount_1", "NUMERIC"),
            _column("Amount", "foreign_amount_2", "NUMERIC"),
            _column("Amount", "foreign_amount_3", "NUMERIC"),
        ],
    )

    with pytest.raises(CliError) as math_error:
        service.call_view(
            LOCAL_VIEW,
            "math",
            dataset_id=LOCAL_DATASET,
            expression="Amount * 2",
            new_column="Total",
            condition={"column": "Amount", "operator": "GTE", "value": 1},
        )
    assert math_error.value.code == "unknown_column"

    with pytest.raises(CliError) as join_error:
        service.call_view(
            LOCAL_VIEW,
            "join",
            dataset_id=LOCAL_DATASET,
            foreign_view=FOREIGN_VIEW,
            foreign_dataset_id=FOREIGN_DATASET,
            join_type="LEFT",
            on=[{"left": "Amount", "right": "Amount"}],
            select=["Amount"],
        )
    assert join_error.value.code == "unknown_column"

    assert _posts(api) == []


def test_join_resolves_foreign_display_names_at_exact_foreign_parent(
    real_service: ServiceFactory,
) -> None:
    service, api = real_service(project_id=PROJECT_ID)
    _configure(
        api,
        local=[_column("Customer ID", "local_customer")],
        foreign=[
            _column('Name "quoted"', "foreign_name"),
            _column("SELECT", "foreign_select"),
        ],
    )

    service.call_view(
        LOCAL_VIEW,
        "join",
        dataset_id=LOCAL_DATASET,
        foreign_view=FOREIGN_VIEW,
        foreign_dataset_id=FOREIGN_DATASET,
        join_type="LEFT",
        on=[{"left": "Customer ID", "right": 'Name "quoted"'}],
        select=['Name "quoted"', "SELECT"],
    )

    assert _has_path(api, f"/datasets/{FOREIGN_DATASET}/dataviews/{FOREIGN_VIEW}")
    assert not _has_path(api, f"/datasets/999/dataviews/{FOREIGN_VIEW}")
    assert len(_posts(api)) == 1
    join = _posts(api)[0].json_body["JOIN"]
    assert join["ON"] == [{"LEFT": "local_customer", "RIGHT": "foreign_name"}]
    assert join["SELECT"] == [
        {"COLUMN": "foreign_name", "ALIAS": 'Name "quoted"'},
        {"COLUMN": "foreign_select", "ALIAS": "SELECT"},
    ]


def test_unknown_foreign_join_name_and_internal_lookup_ids_do_not_post(
    real_service: ServiceFactory,
) -> None:
    service, api = real_service(project_id=PROJECT_ID)
    _configure(
        api,
        local=[_column("Customer ID", "local_customer")],
        foreign=[_column("SKU 名", "foreign_sku"), _column("SELECT", "foreign_value")],
    )

    with pytest.raises(CliError) as join_error:
        service.call_view(
            LOCAL_VIEW,
            "join",
            dataset_id=LOCAL_DATASET,
            foreign_view=FOREIGN_VIEW,
            foreign_dataset_id=FOREIGN_DATASET,
            join_type="LEFT",
            on=[{"left": "Customer ID", "right": "Not in foreign view"}],
            select=["SELECT"],
        )
    assert join_error.value.code == "unknown_column"
    assert _posts(api) == []

    service2, api2 = real_service(project_id=PROJECT_ID)
    _configure(
        api2,
        local=[_column("Source", "local_source")],
        foreign=[_column("SKU 名", "foreign_sku"), _column("SELECT", "foreign_value")],
    )
    with pytest.raises(CliError) as lookup_error:
        service2.call_view(
            LOCAL_VIEW,
            "lookup",
            dataset_id=LOCAL_DATASET,
            source="Source",
            lookup_view_id=FOREIGN_VIEW,
            lookup_dataset_id=FOREIGN_DATASET,
            key="foreign_sku",
            value="SELECT",
            new_column="Result",
        )
    assert lookup_error.value.code == "internal_column_name"
    assert _posts(api2) == []


def test_lookup_resolves_unicode_foreign_names_and_posts_once(real_service: ServiceFactory) -> None:
    service, api = real_service(project_id=PROJECT_ID)
    _configure(
        api,
        local=[_column("Source 名", "local_source")],
        foreign=[_column("SKU 名", "foreign_sku"), _column("SELECT", "foreign_value")],
    )

    service.call_view(
        LOCAL_VIEW,
        "lookup",
        dataset_id=LOCAL_DATASET,
        source="Source 名",
        lookup_view_id=FOREIGN_VIEW,
        lookup_dataset_id=FOREIGN_DATASET,
        key="SKU 名",
        value="SELECT",
        new_column="Result 名",
    )

    assert len(_posts(api)) == 1
    lookup = _posts(api)[0].json_body["LOOKUP"]
    assert lookup["SOURCE"] == "local_source"
    assert lookup["KEY"] == "foreign_sku"
    assert lookup["VALUE"] == "foreign_value"
