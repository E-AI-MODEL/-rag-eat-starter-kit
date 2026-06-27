from __future__ import annotations

import unittest

from examples import llm_anthropic_adapter as adapter


class AnthropicAdapterConfigTests(unittest.TestCase):
    def test_model_from_env_uses_default_when_missing_or_blank(self) -> None:
        self.assertEqual(adapter.model_from_env({}), adapter.DEFAULT_MODEL)
        self.assertEqual(adapter.model_from_env({"RAGKIT_MODEL": "   "}), adapter.DEFAULT_MODEL)

    def test_model_from_env_uses_configured_model(self) -> None:
        self.assertEqual(
            adapter.model_from_env({"RAGKIT_MODEL": "custom-model"}),
            "custom-model",
        )

    def test_require_anthropic_api_key_rejects_missing_and_placeholders(self) -> None:
        for env in ({}, {"ANTHROPIC_API_KEY": ""}, {"ANTHROPIC_API_KEY": "..."}):
            with self.subTest(env=env):
                with self.assertRaisesRegex(RuntimeError, "ANTHROPIC_API_KEY"):
                    adapter.require_anthropic_api_key(env)

    def test_require_anthropic_api_key_accepts_non_placeholder(self) -> None:
        self.assertEqual(
            adapter.require_anthropic_api_key({"ANTHROPIC_API_KEY": "sk-ant-test"}),
            "sk-ant-test",
        )


if __name__ == "__main__":
    unittest.main()
