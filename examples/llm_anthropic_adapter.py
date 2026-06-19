"""Example of plugging a real LLM into the kit.

The kit is vendor-neutral: `Assistant` accepts any callable with this signature:
`(system_prompt, question, context) -> str`.

Run it:

    pip install "anthropic>=0.40"
    export ANTHROPIC_API_KEY=...
    python3 examples/llm_anthropic_adapter.py "What are the cancellation conditions?"
"""

from __future__ import annotations

import os
import sys
from typing import List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from ragkit import HybridIndex, load_corpus, load_eat  # noqa: E402
from ragkit.assistant import Assistant  # noqa: E402

MODEL = os.environ.get("RAGKIT_MODEL", "claude-opus-4-8")


def make_anthropic_llm(model: str = MODEL):
    """Return an `llm` callable backed by the Anthropic Messages API."""
    import anthropic

    client = anthropic.Anthropic()

    def llm(system_prompt: str, question: str, context: List[str]) -> str:
        joined = "\n\n---\n\n".join(context)
        user = (
            "Retrieved context, the only source of facts you may use:\n\n"
            f"{joined}\n\nQuestion: {question}"
        )
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in message.content if block.type == "text")

    return llm


def main(argv: List[str]) -> int:
    question = argv[0] if argv else "What are the cancellation conditions?"
    profile = load_eat(os.path.join(ROOT, "prompts", "rag_assistant.eat"))
    index = HybridIndex(load_corpus(os.path.join(ROOT, "examples", "corpus")))
    llm = make_anthropic_llm()
    assistant = Assistant(profile, index, user_groups=["public", "support"], llm=llm)
    result = assistant.answer(question)
    print(result.answer)
    if result.citations:
        print("\nSources:")
        for c in result.citations:
            print(f"- {c.chunk.citation()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
