"""Real-code tests for SDK-signature-derived argument specs.

These resolve real ``sdk_symbol`` values from the manifests against the real
SDK and assert the derived accepted-field sets match the actual method
signatures. No mocks: the whole point is that the spec tracks the live SDK.
"""

from __future__ import annotations

from mammoth_cli.services.argspec import (
    accepted_field_names,
    arg_spec,
)


def test_view_transform_fields_match_signature() -> None:
    """A View transform's accepted fields equal its real parameters."""
    spec = arg_spec("mammoth.view.View.bulk_replace")
    assert spec is not None
    assert spec.field_names == {"columns", "mapping", "match_case", "match_words", "condition"}
    assert spec.required_names == ("columns", "mapping")
    assert spec.accepts_extra is False


def test_subclient_method_fields() -> None:
    """A sub-client method resolves to its parameters."""
    assert accepted_field_names("mammoth.api.pipeline.PipelineAPI.get_draft_status") == {
        "dataview_id",
        "dataset_id",
    }


def test_fixed_signature_method_field_set() -> None:
    """A method with a fixed signature yields its exact field set."""
    assert accepted_field_names("mammoth.api.projects.ProjectsAPI.create") == {
        "name",
        "color",
        "project_access",
        "workspace_id",
    }


def test_var_keyword_method_accepts_anything() -> None:
    """A method with **kwargs accepts any field, so enforcement is disabled."""
    # ActivityLogsAPI.list has a **kwargs catch-all, so no key can be proven
    # invalid and strict enforcement is intentionally disabled.
    assert accepted_field_names("mammoth.api.activity_logs.ActivityLogsAPI.list") is None
    assert arg_spec("mammoth.api.activity_logs.ActivityLogsAPI.list").accepts_extra is True


def test_private_symbol_is_refused() -> None:
    """A private-member symbol never resolves."""
    assert arg_spec("mammoth.view.View._add_task") is None


def test_unresolvable_symbol_returns_none() -> None:
    """An unknown symbol yields None so callers fall back to non-strict."""
    assert arg_spec("mammoth.nope.Nothing.missing") is None
    assert accepted_field_names("mammoth.nope.Nothing.missing") is None
