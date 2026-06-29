"""The assistant: EAT system prompt + retrieval, answering from context only.

Vendor-neutral by design. If you pass an `llm` callable, it is called with the
EAT-rendered system prompt, the user question and the retrieved context. If you
pass nothing, an offline extractive fallback runs so the whole loop is
reproducible without credentials.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .eat_loader import EATProfile
from .retrieval import ScoredChunk
from .retriever import Retriever

# An LLM is any callable: (system_prompt, question, context_blocks) -> answer text.
LLM = Callable[[str, str, List[str]], str]


@dataclass
class AnswerResult:
    question: str
    answer: str
    abstained: bool
    citations: List[ScoredChunk] = field(default_factory=list)

    @property
    def cited_sources(self) -> List[str]:
        return [c.chunk.source_id for c in self.citations]

    @property
    def cited_families(self) -> List[str]:
        return [c.chunk.family for c in self.citations]


_FALLBACK = (
    "I cannot answer this reliably based on the retrieved sources. "
    "The available context does not contain a reliable passage that supports this question."
)


class Assistant:
    def __init__(
        self,
        profile: EATProfile,
        index: Retriever,
        user_groups: Sequence[str],
        top_k: int = 4,
        llm: Optional[LLM] = None,
    ):
        self.profile = profile
        self.index = index
        self.user_groups = list(user_groups)
        self.top_k = top_k
        self.llm = llm
        self.system_prompt = profile.render_system_prompt()

    def answer(self, question: str) -> AnswerResult:
        hits = self.index.search(question, self.user_groups, top_k=self.top_k)

        if not hits:
            # No supporting, accessible context -> abstain.
            return AnswerResult(question, _FALLBACK, abstained=True, citations=[])

        if self.llm is not None:
            context = [f"{h.chunk.citation()}\n{h.chunk.text}" for h in hits]
            text = self.llm(self.system_prompt, question, context)
            return AnswerResult(question, text, abstained=False, citations=hits)

        return AnswerResult(question, self._extractive(hits), abstained=False, citations=hits)

    def _extractive(self, hits: List[ScoredChunk]) -> str:
        top = hits[0].chunk
        lines = [
            f"Based on the retrieved sources, {top.section or top.title} addresses this.",
            "",
            "Answer:",
            top.text.strip(),
            "",
            "Sources:",
        ]
        seen = set()
        for h in hits:
            if h.chunk.source_id in seen:
                continue
            seen.add(h.chunk.source_id)
            lines.append(f"- {h.chunk.citation()}")
        return "\n".join(lines)
