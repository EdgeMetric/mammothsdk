"""Every command's positionals are declared with native Typer type + requiredness.

Review finding (fifth pass): positionals were declared uniformly as optional
``str | None`` at the Typer layer, so ``--help`` misreported a required integer id
as an optional string (``[DATASET_ID] <str>`` instead of ``DATASET_ID <int>
[required]``). This guards the fix: for every manifest command, the Typer
``Argument`` parameter built from each :class:`PositionalSpec` must carry the
spec's real scalar type and requiredness, so the rendered help and the parser can
never drift from the single positional source of truth again.
"""

from __future__ import annotations

import inspect
import typing

import pytest

from mammoth_cli import app
from mammoth_cli.manifest.loader import load_commands
from mammoth_cli.services.positionals import resolve_positionals


def _command_ids() -> list[str]:
    return [
        record["command_id"]
        for record in load_commands()
        if record.get("disposition") != "alias"
    ]


def _unwrap_annotated(annotation: object) -> object:
    """Return the underlying type of an ``Annotated[...]`` parameter annotation."""
    if hasattr(annotation, "__metadata__"):
        return typing.get_args(annotation)[0]
    return annotation


@pytest.mark.parametrize("command_id", _command_ids())
def test_positional_param_matches_spec(command_id: str) -> None:
    """Each positional's Typer parameter mirrors its spec's type and requiredness."""
    for spec in resolve_positionals(command_id):
        param = app._positional_param(spec)
        inner = _unwrap_annotated(param.annotation)
        assert param.name == spec.name
        if spec.required:
            # A required positional has no default: Typer enforces presence and
            # renders it as required, and the annotation is the bare scalar type.
            assert param.default is inspect.Parameter.empty, command_id
            assert inner is spec.type, (command_id, spec.name, inner)
        else:
            # An optional positional defaults to None and is Optional[scalar].
            assert param.default is None, command_id
            union_args = typing.get_args(inner)
            assert spec.type in union_args, (command_id, spec.name, union_args)
            assert type(None) in union_args, (command_id, spec.name, union_args)


def test_at_least_one_required_int_and_one_optional_positional_covered() -> None:
    """Sanity: the parametrized sweep actually exercises both shapes.

    Without this, a refactor that silently emptied ``resolve_positionals`` would
    make the sweep vacuously pass. ``dataset.get`` is a required ``int`` id;
    ``project.create`` is an optional ``str`` name (positional or --input).
    """
    dataset_get = resolve_positionals("dataset.get")
    assert any(s.required and s.type is int for s in dataset_get), dataset_get
    project_create = resolve_positionals("project.create")
    assert any(not s.required and s.type is str for s in project_create), project_create
