"""Typed pagination models.

Several list endpoints return an offset-based envelope. Public SDK list methods
should return a typed ``Page`` so callers get pagination metadata instead of a
bare list, and so a CLI can offer ``--all`` only against a proven continuation
contract.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """One page of an offset-paginated collection.

    Attributes:
        items: The records on this page.
        offset: The offset this page started at.
        limit: The page size requested.
        total: The total record count when the server reports it.
    """

    items: list[T] = Field(default_factory=list)
    offset: int = 0
    limit: int | None = None
    total: int | None = None

    @property
    def next_offset(self) -> int | None:
        """The offset for the next page, or ``None`` when the page is the last."""
        if not self.items:
            return None
        candidate = self.offset + len(self.items)
        if self.total is not None and candidate >= self.total:
            return None
        if self.limit is not None and len(self.items) < self.limit:
            return None
        return candidate

    @property
    def has_more(self) -> bool:
        """Whether a further page exists under the offset contract."""
        return self.next_offset is not None
