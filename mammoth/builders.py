"""The SDK's pure spec builders, under public names.

Each one turns a step's or an export's arguments into the spec the API takes,
and checks them on the way, with no request sent. The SDK's own methods build
their requests with these, so code that builds a spec itself, such as a server
that sends it later, accepts exactly what the SDK accepts.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from mammoth._pure.builders import (
    _EXPORT_CONTRACTS,
    _TargetContract,
    build_add_column_params,
    build_bulk_replace_params,
    build_combine_params,
    build_convert_params,
    build_copy_params,
    build_date_diff_params,
    build_delete_params,
    build_discard_duplicates_params,
    build_export_spec,
    build_extract_date_params,
    build_fill_params,
    build_fill_value_params,
    build_filter_params,
    build_gen_ai_params,
    build_increment_date_params,
    build_join_params,
    build_json_extract_params,
    build_limit_params,
    build_lookup_params,
    build_math_params,
    build_pivot_params,
    build_replace_params,
    build_set_params,
    build_small_large_params,
    build_split_params,
    build_sql_params,
    build_substring_params,
    build_text_transform_params,
    build_unnest_params,
    build_window_params,
)
from mammoth._pure.resolve import resolve_column
from mammoth.models.exports import HandlerType

#: The settings one export destination takes: `required`, `optional`, the
#: `defaults` an omitted one falls back to, and whether others are allowed.
ExportContract = _TargetContract

#: Every destination the SDK checks the settings of, and how.
EXPORT_CONTRACTS: Mapping[HandlerType, ExportContract] = MappingProxyType(_EXPORT_CONTRACTS)


def export_contract(handler: HandlerType) -> ExportContract | None:
    """The settings one export destination takes, or None when the SDK leaves
    them for the API to check."""
    return EXPORT_CONTRACTS.get(handler)


__all__ = [
    "EXPORT_CONTRACTS",
    "ExportContract",
    "build_add_column_params",
    "build_bulk_replace_params",
    "build_combine_params",
    "build_convert_params",
    "build_copy_params",
    "build_date_diff_params",
    "build_delete_params",
    "build_discard_duplicates_params",
    "build_export_spec",
    "build_extract_date_params",
    "build_fill_params",
    "build_fill_value_params",
    "build_filter_params",
    "build_gen_ai_params",
    "build_increment_date_params",
    "build_join_params",
    "build_json_extract_params",
    "build_limit_params",
    "build_lookup_params",
    "build_math_params",
    "build_pivot_params",
    "build_replace_params",
    "build_set_params",
    "build_small_large_params",
    "build_split_params",
    "build_sql_params",
    "build_substring_params",
    "build_text_transform_params",
    "build_unnest_params",
    "build_window_params",
    "export_contract",
    "resolve_column",
]
