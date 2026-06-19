"""Hybrid retrieval with fail-closed access filtering.

Pure standard library plus PyYAML. No external services, no embeddings download.
Hybrid = BM25 (good for exact terms, codes, names) + TF-IDF cosine (good for
meaning), merged and reranked. Access control is applied *before* scoring and
*fails closed*: a chunk with no group overlap is never even a candidate, so it
can never leak into an answer.
"""

from __future__ import annotations

import glob
import math
import os
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Dict, List

import yaml

_TOKEN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "what", "which", "who",
    "does", "do", "did", "of", "to", "for", "in", "on", "and", "or", "now",
    "this", "that", "it", "its", "with", "as", "by", "at", "from", "should",
    "can", "will", "we", "you", "i", "my", "our",
}


def tokenize(text: str) -> List[str]:
    return _TOKEN.findall(text.lower())


def content_terms(text: str) -> List[str]:
    return [t for t in tokenize(text) if t not in _STOPWORDS]


@dataclass
class Chunk:
    source_id: str
    title: str
    section: str
    text: str
    version: str = ""
    updated_at: str = ""
    family: str = ""
    allowed_groups: List[str] = field(default_factory=list)
    tokens: List[str] = field(default_factory=list)

    def citation(self) -> str:
        bits = [self.title]
        if self.section:
            bits.append(self.section)
        ref = " — ".join(bits)
        if self.version or self.updated_at:
            ref += f" (version {self.version or 'n/a'}, updated {self.updated_at or 'n/a'})"
        return f"{ref}  [{self.source_id}]"


def _split_sections(body: str) -> List[tuple[str, str]]:
    """Split markdown into (heading, text) sections on `#` headings."""
    sections: List[tuple[str, str]] = []
    heading = ""
    buf: List[str] = []
    for line in body.splitlines():
        if line.lstrip().startswith("#"):
            if buf and "".join(buf).strip():
                sections.append((heading, "\n".join(buf).strip()))
            heading = line.lstrip("#").strip()
            buf = []
        else:
            buf.append(line)
    if buf and "".join(buf).strip():
        sections.append((heading, "\n".join(buf).strip()))
    if not sections:
        sections = [("", body.strip())]
    return sections


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            meta = yaml.safe_load(raw[3:end]) or {}
            return meta, raw[end + 4 :].lstrip("\n")
    return {}, raw


def load_corpus(corpus_dir: str) -> List[Chunk]:
    """Load every `*.md` document under `corpus_dir` into access-tagged chunks."""
    chunks: List[Chunk] = []
    for path in sorted(glob.glob(os.path.join(corpus_dir, "*.md"))):
        with open(path, encoding="utf-8") as fh:
            meta, body = _parse_frontmatter(fh.read())
        source_id = str(meta.get("source_id") or os.path.splitext(os.path.basename(path))[0])
        groups = meta.get("allowed_groups") or []
        if isinstance(groups, str):
            groups = [groups]
        for heading, text in _split_sections(body):
            chunks.append(
                Chunk(
                    source_id=source_id,
                    title=str(meta.get("title") or source_id),
                    section=heading,
                    text=text,
                    version=str(meta.get("version") or ""),
                    updated_at=str(meta.get("updated_at") or ""),
                    family=str(meta.get("family") or source_id),
                    allowed_groups=[str(g) for g in groups],
                    tokens=tokenize(f"{meta.get('title', '')} {heading} {text}"),
                )
            )
    return chunks


def _minmax(scores: Dict[int, float]) -> Dict[int, float]:
    if not scores:
        return {}
    lo, hi = min(scores.values()), max(scores.values())
    if hi - lo < 1e-12:
        return {k: 1.0 for k in scores}
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


@dataclass
class ScoredChunk:
    chunk: Chunk
    score: float


class HybridIndex:
    """BM25 + TF-IDF cosine over a fixed set of chunks, filtered per user."""

    def __init__(self, chunks: Sequence[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = list(chunks)
        self.k1 = k1
        self.b = b

    def _accessible(self, user_groups: Sequence[str]) -> List[int]:
        allowed = set(user_groups)
        # Fail closed: no metadata or no overlap => not a candidate.
        return [
            i
            for i, c in enumerate(self.chunks)
            if c.allowed_groups and (set(c.allowed_groups) & allowed)
        ]

    def _bm25(self, q_terms: List[str], idxs: List[int]) -> Dict[int, float]:
        n = len(idxs)
        if n == 0:
            return {}
        docs = {i: Counter(self.chunks[i].tokens) for i in idxs}
        avgdl = sum(len(self.chunks[i].tokens) for i in idxs) / n
        df = {t: sum(1 for i in idxs if t in docs[i]) for t in set(q_terms)}
        scores: Dict[int, float] = {}
        for i in idxs:
            dl = len(self.chunks[i].tokens) or 1
            s = 0.0
            for t in q_terms:
                f = docs[i].get(t, 0)
                if not f:
                    continue
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                s += idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * dl / avgdl))
            if s > 0:
                scores[i] = s
        return scores

    def _tfidf_cosine(self, q_terms: List[str], idxs: List[int]) -> Dict[int, float]:
        n = len(idxs)
        if n == 0:
            return {}
        docs = {i: Counter(self.chunks[i].tokens) for i in idxs}
        vocab = set(q_terms) | {t for i in idxs for t in docs[i]}
        df = {t: sum(1 for i in idxs if t in docs[i]) for t in vocab}
        idf = {t: math.log((n + 1) / (df[t] + 1)) + 1 for t in vocab}

        def vec(counts: Counter) -> Dict[str, float]:
            return {t: counts[t] * idf[t] for t in counts}

        qv = vec(Counter(q_terms))
        qn = math.sqrt(sum(v * v for v in qv.values())) or 1.0
        scores: Dict[int, float] = {}
        for i in idxs:
            dv = vec(docs[i])
            dn = math.sqrt(sum(v * v for v in dv.values())) or 1.0
            dot = sum(qv.get(t, 0.0) * dv.get(t, 0.0) for t in qv)
            if dot > 0:
                scores[i] = dot / (qn * dn)
        return scores

    def search(
        self,
        query: str,
        user_groups: Sequence[str],
        top_k: int = 5,
        require_overlap: bool = True,
        min_ratio: float = 0.3,
    ) -> List[ScoredChunk]:
        idxs = self._accessible(user_groups)
        q_terms = content_terms(query)
        if not q_terms:
            return []

        bm25 = _minmax(self._bm25(q_terms, idxs))
        tfidf = _minmax(self._tfidf_cosine(q_terms, idxs))
        combined: Dict[int, float] = {}
        for i in set(bm25) | set(tfidf):
            combined[i] = 0.5 * bm25.get(i, 0.0) + 0.5 * tfidf.get(i, 0.0)

        if require_overlap:
            q_set = set(q_terms)
            combined = {
                i: s for i, s in combined.items() if q_set & set(self.chunks[i].tokens)
            }

        # Drop weak co-matches so we only cite genuinely supporting passages.
        if combined:
            floor = max(combined.values()) * min_ratio
            combined = {i: s for i, s in combined.items() if s >= floor}

        ranked = sorted(combined.items(), key=lambda kv: kv[1], reverse=True)

        # Prefer the latest source within a family (metadata-driven dedup).
        best_in_family: Dict[str, int] = {}
        order: List[int] = []
        for i, _ in ranked:
            fam = self.chunks[i].family
            prev = best_in_family.get(fam)
            if prev is None:
                best_in_family[fam] = i
                order.append(i)
            elif self.chunks[i].updated_at > self.chunks[prev].updated_at:
                # Replace the older family member already in the order.
                order[order.index(prev)] = i
                best_in_family[fam] = i

        return [ScoredChunk(self.chunks[i], combined[i]) for i in order[:top_k]]
