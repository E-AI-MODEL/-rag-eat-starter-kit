"""Tests for the Retriever protocol extension point."""

from __future__ import annotations

import os
import sys
import unittest
from collections.abc import Sequence
from typing import List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from ragkit import HybridIndex, load_eat  # noqa: E402
from ragkit.assistant import Assistant  # noqa: E402
from ragkit.retrieval import Chunk, ScoredChunk  # noqa: E402
from ragkit.retriever import Retriever  # noqa: E402

EAT_PATH = os.path.join(ROOT, "prompts", "rag_assistant.eat")


def _chunk(source_id: str, text: str, groups=None, family=None) -> Chunk:
    return Chunk(
        source_id=source_id,
        title=source_id,
        section="",
        text=text,
        family=family or source_id,
        allowed_groups=groups or ["public"],
        tokens=text.lower().split(),
    )


class _CustomRetriever:
    def __init__(self, chunks: List[Chunk]):
        self.chunks = chunks

    def search(
        self,
        query: str,
        user_groups: Sequence[str],
        top_k: int = 5,
    ) -> List[ScoredChunk]:
        allowed = set(user_groups)
        candidates = [
            c for c in self.chunks
            if c.allowed_groups and (set(c.allowed_groups) & allowed)
        ]
        q_terms = set(query.lower().split())
        scored = [
            ScoredChunk(c, len(set(c.tokens) & q_terms) / max(len(q_terms), 1))
            for c in candidates
            if set(c.tokens) & q_terms
        ]
        return scored[:top_k]


class _NoChunksRetriever:
    def __init__(self, result: ScoredChunk):
        self.result = result

    def search(
        self,
        query: str,
        user_groups: Sequence[str],
        top_k: int = 5,
    ) -> List[ScoredChunk]:
        return [self.result]


class TestProtocolConformance(unittest.TestCase):
    def test_hybrid_index_satisfies_retriever_protocol(self):
        idx = HybridIndex([_chunk("doc", "test content")])
        self.assertIsInstance(idx, Retriever)

    def test_custom_retriever_satisfies_protocol(self):
        r = _CustomRetriever([_chunk("doc", "test content")])
        self.assertIsInstance(r, Retriever)

    def test_plain_object_without_search_does_not_satisfy(self):
        class _NotARetriever:
            pass

        self.assertNotIsInstance(_NotARetriever(), Retriever)


class TestAssistantWithCustomRetriever(unittest.TestCase):
    def setUp(self):
        self.profile = load_eat(EAT_PATH)
        self.chunks = [
            _chunk("public_doc", "public cancellation terms", groups=["public"]),
            _chunk("finance_doc", "secret pricing markup", groups=["finance"]),
        ]

    def test_assistant_accepts_custom_retriever(self):
        a = Assistant(
            self.profile,
            _CustomRetriever(self.chunks),
            user_groups=["public"],
        )
        result = a.answer("cancellation")
        self.assertFalse(result.abstained)
        self.assertIn("public_doc", result.cited_sources)

    def test_fail_closed_with_custom_retriever(self):
        a = Assistant(
            self.profile,
            _CustomRetriever(self.chunks),
            user_groups=["public"],
        )
        result = a.answer("pricing markup")
        self.assertTrue(result.abstained)
        self.assertNotIn("finance_doc", result.cited_sources)

    def test_finance_user_can_see_finance_doc(self):
        a = Assistant(
            self.profile,
            _CustomRetriever(self.chunks),
            user_groups=["finance"],
        )
        result = a.answer("pricing markup")
        self.assertFalse(result.abstained)
        self.assertIn("finance_doc", result.cited_sources)


if __name__ == "__main__":
    unittest.main()
