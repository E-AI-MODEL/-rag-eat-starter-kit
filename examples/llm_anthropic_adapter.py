"""A worked example of plugging a real LLM into the kit.

The kit is vendor-neutral: `Assistant` accepts any callable with the signature
`(system_prompt, question, context) -> str`. This file shows one concrete adapter,
built on the Anthropic SDK, so the demo can answer with a real model instead of the
offline extractive fallback. Swap in any other provider by writing the same callable.

Run it:

    pip install "anthropic>=0.40"        # not required for the offline demo
    export ANTHROPIC_API_KEY=...         # your key
    python3 examples/llm_anthropic_adapter.py "What are the cancellation conditions?"

The safety contract is unchanged: retrieval + access filtering happen first, so the
model only ever sees context the user is allowed to see, and the assistant still
abstains when nothing supports the question.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from ragkit import HybridIndex, load_corpus, load_eat  # noqa: E402
from ragkit.assistant import Assistant  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.environ.get("RAGKIT_MODEL", "claude-opus-4-8")


def make_anthropic_llm(model: str = MODEL):
    """Return an `llm` callable backed by the Anthropic Messages API."""
    import anthropic  # imported lazily so the offline demo needs no dependency

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    def llm(system_prompt: str, question: str, context: list[str]) -> str:
        joined = "\n\n---\n\n".join(context)
        user = (
            f"Retrieved context (the only source of facts you may use):\n\n{joined}\n\n"
            f"Question: {question}"
        )
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,  # the EAT-rendered behavior contract
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in message.content if block.type == "text")

    return llm


def main(argv: list[str]) -> int:
    question = argv[0] if argv else "What are the cancellation conditions?"
    profile = load_eat(os.path.join(ROOT, "prompts", "rag_assistant.eat"))
    index = HybridIndex(load_corpus(os.path.join(ROOT, "examples", "corpus")))
    assistant = Assistant(
        profile, index, user_groups=["public", "support"], llm=make_anthropic_llm()
    )
    result = assistant.answer(question)
    print(result.answer)
    if result.citations:
        print("\nSources:")
        for c in result.citations:
            print(f"- {c.chunk.citation()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
