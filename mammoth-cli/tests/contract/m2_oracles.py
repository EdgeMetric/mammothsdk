"""Frozen M2 wire/dispatch oracles authored independently of the resolver.

These values describe the public handler-to-SDK boundary.  They are deliberately
plain literals: this fixture must not import ``command_contract`` or derive an
expected request from SDK introspection, otherwise a dropped binding could make
its own test pass.
"""

from __future__ import annotations

ZERO_INPUT_ORACLE = {
    "sdk_symbol": "mammoth.api.dashboards.DashboardsAPI.get_sources",
    "kwargs": {},
}
UPLOAD_POSITIONAL_ORACLE = {
    "sdk_symbol": "mammoth.api.files.FilesAPI.upload",
    "kwargs": {
        "files": ["./pilot-positional.csv"],
        "folder_resource_id": "folder-sentinel",
        "append_to_ds_id": 731,
        "override_target_schema": True,
        "wait_for_completion": False,
        "timeout": 47,
    },
}

UPLOAD_INPUT_ORACLE = {
    "sdk_symbol": "mammoth.api.files.FilesAPI.upload",
    "kwargs": {
        "files": ["./pilot-input.csv"],
        "folder_resource_id": "folder-input-sentinel",
        "append_to_ds_id": 732,
        "override_target_schema": False,
        "wait_for_completion": False,
        "timeout": 48,
    },
}

MATH_CONDITION_ORACLE = {
    "view_id": 41,
    "method": "math",
    "kwargs": {
        "expression": "Revenue * Units",
        "new_column": "Pilot total",
        "column_type": "NUMERIC",
        "existing_column": None,
        "condition": {"column": "Region", "operator": "EQ", "value": "West"},
    },
}

FOREIGN_LOOKUP_ORACLE = {
    "view_id": 42,
    "method": "lookup",
    "kwargs": {
        "source": "Customer ID",
        "lookup_view_id": 9002,
        "key": "Customer ID",
        "value": "Annual revenue",
        "new_column": "Revenue from foreign view",
        "new_column_type": "NUMERIC",
        "existing_column": None,
    },
}
