"""Tests for the release-notes extractor. Run: python3 -m unittest -v"""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import changelog_extract as ce  # noqa: E402

SAMPLE = """# Changelog

## [Unreleased]

## [0.1.0] - 2026-06-20

### Added
- thing one
- thing two

## [0.0.9] - 2026-01-01

### Added
- old thing
"""


class TestChangelogExtract(unittest.TestCase):
    def test_extracts_only_the_requested_section(self):
        body = ce.extract(SAMPLE, "0.1.0")
        self.assertIn("thing one", body)
        self.assertIn("thing two", body)
        self.assertNotIn("old thing", body)
        self.assertNotIn("## [0.1.0]", body)

    def test_leading_v_is_stripped(self):
        self.assertEqual(ce.extract(SAMPLE, "v0.1.0"), ce.extract(SAMPLE, "0.1.0"))

    def test_missing_version_is_empty(self):
        self.assertEqual(ce.extract(SAMPLE, "9.9.9"), "")

    def test_empty_unreleased_is_empty(self):
        self.assertEqual(ce.extract(SAMPLE, "Unreleased").strip(), "")

    def test_real_changelog_has_a_0_1_0_section(self):
        with open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8") as fh:
            self.assertTrue(ce.extract(fh.read(), "0.1.0").strip())


if __name__ == "__main__":
    unittest.main()
