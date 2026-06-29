from __future__ import annotations

from collections.abc import Sequence
from typing import List, Protocol, runtime_checkable

from .retrieval import ScoredChunk


@runtime_checkable
class Retriever(Protocol):
    """Minimal protocol for pluggable retrieval backends."""

    def search(
        self,
        query: str,
        user_groups: Sequence[str],
        top_k: int = 5,
    ) -> List[ScoredChunk]:
        """Return up to `top_k` chunks for `query` that match `user_groups`."""
        ...
