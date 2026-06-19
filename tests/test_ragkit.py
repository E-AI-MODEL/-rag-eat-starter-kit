"""Tests that the kit's claims actually hold. Run: python3 -m unittest -v"""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from ragkit import HybridIndex, load_corpus, load_eat  # noqa: E402
from ragkit.assistant import Assistant  # noqa: E402
from ragkit.eat_loader import EATValidationError, _parse  # noqa: E402
from ragkit.eval_runner import run_eval  # noqa: E402

EAT_PATH = os.path.join(ROOT, "prompts", "rag_assistant.eat")
CORPUS_DIR = os.path.join(ROOT, "examples", "corpus")
EVAL_CSV = os.path.join(ROOT, "eval", "rag_eval_set.csv")
PUBLIC_USER = ["public", "support"]


def build_assistant(groups=PUBLIC_USER):
    return Assistant(load_eat(EAT_PATH), HybridIndex(load_corpus(CORPUS_DIR)), groups)


class TestEATValidation(unittest.TestCase):
    def test_real_profile_loads_and_renders(self):
        profile = load_eat(EAT_PATH)
        self.assertTrue(profile.locked)
        self.assertEqual(len(profile.table("workflow")), 7)
        self.assertIn("Workflow:", profile.render_system_prompt())

    def test_row_count_mismatch_is_rejected(self):
        bad = "workflow[2]{step, action}:\n  a, do_a\n"
        with self.assertRaises(EATValidationError):
            _parse(bad)

    def test_typed_array_without_columns_is_rejected(self):
        with self.assertRaises(EATValidationError):
            _parse("workflow[1]:\n  a\n")

    def test_non_identifier_cell_is_rejected(self):
        with self.assertRaises(EATValidationError):
            _parse("t[1]{a, b}:\n  ok, not an identifier\n")


class TestAccessControl(unittest.TestCase):
    def test_finance_doc_hidden_from_public_user(self):
        a = build_assistant(["public", "support"])
        res = a.answer("What is the internal pricing markup?")
        self.assertTrue(res.abstained)
        self.assertNotIn("internal_pricing", res.cited_sources)

    def test_finance_user_can_see_finance_doc(self):
        a = build_assistant(["finance"])
        res = a.answer("What is the internal pricing markup?")
        self.assertFalse(res.abstained)
        self.assertIn("internal_pricing", res.cited_sources)


class TestRetrievalBehavior(unittest.TestCase):
    def test_prefers_latest_in_family(self):
        a = build_assistant()
        res = a.answer("Which product guide version applies now?")
        self.assertIn("product_guide_v2", res.cited_sources)
        self.assertNotIn("product_guide_v1", res.cited_sources)

    def test_abstains_without_supporting_source(self):
        a = build_assistant()
        self.assertTrue(a.answer("What is the CEO home address?").abstained)


class TestEvalSet(unittest.TestCase):
    def test_all_eval_cases_pass(self):
        results = run_eval(build_assistant(), EVAL_CSV)
        failed = [r.id for r in results if not r.passed]
        self.assertEqual(failed, [], f"failing cases: {failed}")


if __name__ == "__main__":
    unittest.main()
