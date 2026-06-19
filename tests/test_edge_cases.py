"""Regression tests for retrieval, front matter and EAT validation edge cases."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from ragkit import Chunk, HybridIndex  # noqa: E402
from ragkit.eat_loader import EATValidationError, _parse  # noqa: E402
from ragkit.retrieval import _parse_date, _parse_frontmatter  # noqa: E402


def chunk(source_id: str, text: str, groups=None, family=None, updated_at="") -> Chunk:
    return Chunk(
        source_id=source_id,
        title=source_id,
        section="",
        text=text,
        updated_at=updated_at,
        family=family or source_id,
        allowed_groups=groups or ["public"],
        tokens=text.lower().split(),
    )


class TestRetrievalEdgeCases(unittest.TestCase):
    def test_empty_index(self):
        idx = HybridIndex([])
        self.assertEqual(idx.search("any query", user_groups=["public"]), [])

    def test_all_documents_filtered(self):
        idx = HybridIndex([chunk("doc", "test content", groups=["public"])])
        self.assertEqual(idx.search("test", user_groups=["private"]), [])

    def test_equal_scores_do_not_drop_results(self):
        idx = HybridIndex([
            chunk("doc1", "test content", family="doc1"),
            chunk("doc2", "test content", family="doc2"),
        ])
        results = idx.search("test", user_groups=["public"])
        self.assertEqual(len(results), 2)
        self.assertTrue(all(result.score > 0 for result in results))

    def test_unicode_query_does_not_crash(self):
        idx = HybridIndex([chunk("doc", "test content")])
        results = idx.search("query with special chars: abc", user_groups=["public"])
        self.assertIsInstance(results, list)


class TestFrontmatterEdgeCases(unittest.TestCase):
    def test_horizontal_rule_in_body(self):
        raw = "---\ntitle: test\n---\n\nSome text\n---\nMore text\n"
        meta, body = _parse_frontmatter(raw)
        self.assertEqual(meta, {"title": "test"})
        self.assertIn("More text", body)

    def test_invalid_date_format_is_rejected(self):
        with self.assertRaises(ValueError):
            _parse_date("01/01/2024")

    def test_missing_date_is_allowed(self):
        self.assertEqual(_parse_date(None), "")
        self.assertEqual(_parse_date(""), "")


class TestEATRequiredBlocks(unittest.TestCase):
    def test_missing_identity_is_rejected(self):
        with self.assertRaises(EATValidationError):
            _parse("rules:\n  answer_only_from_context\n")

    def test_missing_rules_is_rejected(self):
        with self.assertRaises(EATValidationError):
            _parse("identity:\n  rag_assistant\n")


if __name__ == "__main__":
    unittest.main()
