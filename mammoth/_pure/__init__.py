"""Pure (no-HTTP, no-View) parameter builders for Mammoth pipeline operations.

These modules can be imported and used by backend agents or any caller that
has column metadata as plain dicts, without needing a View or HTTP client.

Public API::

    from mammoth._pure.resolve import resolve_column, resolve_columns, build_as_column
    from mammoth._pure.builders import (
        build_convert_params,
        build_text_transform_params,
        build_replace_params,
        build_bulk_replace_params,
        build_split_params,
        build_substring_params,
        build_add_column_params,
        build_delete_params,
        build_copy_params,
        build_combine_params,
        build_filter_params,
        build_set_params,
        build_math_params,
        build_fill_params,
        build_fill_value_params,
        build_limit_params,
        build_discard_duplicates_params,
        build_unnest_params,
        build_extract_date_params,
        build_date_diff_params,
        build_increment_date_params,
        build_pivot_params,
        build_window_params,
        build_crosstab_params,
        build_branch_out_params,
        build_join_params,
        build_lookup_params,
        build_json_extract_params,
        build_gen_ai_params,
        build_date_normalize_params,
        build_sql_params,
        build_export_spec,
        build_dashboard_gen_spec,
    )
"""

from __future__ import annotations
