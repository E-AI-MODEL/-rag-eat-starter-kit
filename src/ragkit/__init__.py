"""ragkit: a small, vendor-neutral RAG core driven by an EAT behavior profile.

The point of this package is to prove the rest of the starter kit:

- `eat_loader` parses and validates the `.eat` profile and renders the system prompt.
- `retrieval` does hybrid (BM25 + TF-IDF) retrieval with fail-closed access filtering.
- `retriever` defines the pluggable retrieval protocol.
- `assistant` ties the EAT system prompt to retrieval and answers from context only.
- `eval_runner` runs `eval/rag_eval_set.csv` and reports pass/fail.

Everything runs locally on the standard library plus PyYAML. No API keys required.
"""

from .assistant import AnswerResult, Assistant
from .eat_loader import EATProfile, EATValidationError, load_eat
from .retrieval import Chunk, HybridIndex, load_corpus
from .retriever import Retriever

__all__ = [
    "EATProfile",
    "EATValidationError",
    "load_eat",
    "Chunk",
    "HybridIndex",
    "load_corpus",
    "Retriever",
    "Assistant",
    "AnswerResult",
]
