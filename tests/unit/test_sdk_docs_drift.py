"""Focused checks for SDK skill/documentation drift.

These tests intentionally cover only the facts that have historically gone stale:
the advertised SDK version, the parent required by ``views.list``, and the
supported ``files.upload`` recipe.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import mammoth
from mammoth.api.files import FilesAPI
from mammoth.client import ViewsResource


_ROOT = Path(__file__).resolve().parents[2]
_SKILL = _ROOT / ".claude" / "skills" / "mammoth-sdk"


def test_skill_version_matches_sdk_distribution() -> None:
    skill = (_SKILL / "SKILL.md").read_text(encoding="utf-8")
    architecture = (_SKILL / "references" / "architecture.md").read_text(encoding="utf-8")

    assert f"v{mammoth.__version__}" in skill
    assert f"v{mammoth.__version__}" in architecture


def test_skill_views_list_documents_required_parent() -> None:
    parameter = inspect.signature(ViewsResource.list).parameters["dataset_id"]
    assert parameter.default is inspect.Parameter.empty

    api_reference = (_SKILL / "references" / "api-reference.md").read_text(encoding="utf-8")
    examples = (_SKILL / "references" / "examples.md").read_text(encoding="utf-8")
    assert "client.views.list(dataset_id=123)" in api_reference
    assert 'client.views.create(dataset_id=ds_id, name="sales-analysis")' in examples
    assert "view = views[0]" not in examples
    assert "views.list()" in api_reference  # prose describing the method
    assert "views.list() no longer" not in api_reference


def test_skill_upload_recipe_matches_files_api_signature() -> None:
    parameters = inspect.signature(FilesAPI.upload).parameters
    assert "dataset_name" not in parameters
    assert "folder_resource_id" in parameters
    assert "append_to_ds_id" in parameters

    files_reference = (_ROOT / "docs" / "api" / "files.md").read_text(encoding="utf-8")
    assert "dataset_name=" not in files_reference
    assert 'client.files.upload("data.csv")' in files_reference
