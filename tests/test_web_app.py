from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

if importlib.util.find_spec("streamlit") is None:
    raise unittest.SkipTest("streamlit is not installed; install the web extra to run web app tests")

import web_app


class WebAppHelperTests(unittest.TestCase):
    def test_parse_groups_deduplicates_and_trims(self) -> None:
        self.assertEqual(
            web_app.parse_groups(" public, support,public , finance "),
            ["public", "support", "finance"],
        )

    def test_parse_groups_rejects_yaml_like_or_spacey_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "Group names"):
            web_app.parse_groups("public, bad: [group]")

        with self.assertRaisesRegex(ValueError, "Group names"):
            web_app.parse_groups("public, finance team")

    def test_markdown_with_frontmatter_generates_valid_yaml(self) -> None:
        content = web_app.markdown_with_frontmatter(
            "Finance Policy.txt",
            "Refunds require written approval.",
            ["public", "support"],
        )
        self.assertTrue(content.startswith("---\n"))

        metadata_text = content.split("---", 2)[1]
        metadata = yaml.safe_load(metadata_text)
        self.assertEqual(metadata["source_id"], "Finance-Policy")
        self.assertEqual(metadata["title"], "Finance Policy")
        self.assertEqual(metadata["allowed_groups"], ["public", "support"])
        self.assertIn("# Finance Policy", content)
        self.assertIn("Refunds require written approval.", content)

    def test_markdown_with_frontmatter_preserves_existing_frontmatter(self) -> None:
        original = "---\nsource_id: existing\n---\n\n# Existing\n"
        self.assertEqual(web_app.markdown_with_frontmatter("x.md", original, ["public"]), original)

    def test_unique_path_does_not_overwrite_existing_uploads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "document.md").write_text("one", encoding="utf-8")
            self.assertEqual(web_app.unique_path(folder, "document.md"), folder / "document-2.md")


if __name__ == "__main__":
    unittest.main()
