"""Tests for transparent gzip corpus loading and boundary enforcement."""

import gzip
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from ragkit.gzip_boundary import compress_file, compress_tree, validate_boundary  # noqa: E402
from ragkit.retrieval import load_corpus  # noqa: E402

DOCUMENT = """---
source_id: compressed_policy
title: Compressed Policy
allowed_groups: [public]
---
# Retention
Records are retained for seven years.
"""


class TestGzipCorpusLoading(unittest.TestCase):
    def test_loads_gzip_markdown_recursively(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "policy.md.gz"
            path.parent.mkdir()
            with gzip.open(path, "wt", encoding="utf-8") as stream:
                stream.write(DOCUMENT)

            chunks = load_corpus(tmp)

            self.assertEqual(len(chunks), 1)
            self.assertEqual(chunks[0].source_id, "compressed_policy")
            self.assertIn("seven years", chunks[0].text)

    def test_uses_filename_without_double_suffix_as_source_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plain.md.gz"
            with gzip.open(path, "wt", encoding="utf-8") as stream:
                stream.write("# Heading\nBody")

            self.assertEqual(load_corpus(tmp)[0].source_id, "plain")

    def test_rejects_plain_and_compressed_copy_of_same_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "policy.md").write_text(DOCUMENT, encoding="utf-8")
            with gzip.open(root / "policy.md.gz", "wt", encoding="utf-8") as stream:
                stream.write(DOCUMENT)

            with self.assertRaisesRegex(ValueError, "Ambiguous corpus document"):
                load_corpus(tmp)


class TestGzipBoundary(unittest.TestCase):
    def test_reproducible_compression(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.jsonl"
            source.write_text('{"value": "repeated repeated repeated"}\n' * 20, encoding="utf-8")
            first = compress_file(source, root / "first.jsonl.gz")
            second = compress_file(source, root / "second.jsonl.gz")

            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_boundary_rejects_plain_and_invalid_gzip_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "plain.csv").write_text("a,b\n1,2\n", encoding="utf-8")
            (root / "broken.json.gz").write_bytes(b"not gzip")

            violations = validate_boundary(root)

            self.assertEqual(len(violations), 2)

    def test_boundary_allows_readme_and_valid_gzip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("instructions", encoding="utf-8")
            source = root / "outside.txt"
            source.write_text("payload", encoding="utf-8")
            compress_file(source, root / "payload.txt.gz")
            source.unlink()

            self.assertEqual(validate_boundary(root), [])

    def test_compress_tree_preserves_relative_paths_and_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = root / "source"
            destination_root = root / "compressed"
            (source_root / "nested").mkdir(parents=True)
            large = source_root / "nested" / "records.jsonl"
            large.write_text("x" * 100, encoding="utf-8")
            (source_root / "small.txt").write_text("small", encoding="utf-8")

            created = compress_tree(source_root, destination_root, threshold=10)

            self.assertEqual(created, [destination_root / "nested" / "records.jsonl.gz"])
            self.assertTrue(created[0].exists())
            self.assertTrue(large.exists())


if __name__ == "__main__":
    unittest.main()