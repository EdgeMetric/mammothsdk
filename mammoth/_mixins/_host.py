"""Typing-only Protocol describing the host View that the ops mixins extend.

The ops mixins (``ColumnOpsMixin``, ``FilterOpsMixin``, ...) are never used on
their own — they are composed into :class:`mammoth.view.View`, which supplies
the column metadata and task-submission plumbing they call. This Protocol
declares that surface so static type checkers can resolve ``self.columns``,
``self._add_task(...)`` and friends inside the mixins.

It has NO runtime effect: each mixin inherits it only under ``TYPE_CHECKING``
(``else: ViewHost = object``), so at runtime the base is plain ``object`` and
the MRO is unchanged.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from mammoth.view import View


class ViewHost(Protocol):
    """The :class:`~mammoth.view.View` surface the ops mixins rely on."""

    _client: Any
    id: int
    dataset_id: int
    columns: dict[str, str]
    column_types: dict[str, str]
    _internal_names: list[str]

    def _add_task(self, task_spec: dict[str, Any]) -> dict[str, Any]: ...

    def _next_internal_name(self) -> str: ...

    def list_tasks(self) -> list[dict[str, Any]]: ...

    def refresh(self) -> View: ...
