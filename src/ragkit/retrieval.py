"""Hybrid retrieval with access filtering.

The module implements a small local retrieval stack: BM25 for exact terms, TF-IDF
cosine for broader matching, score merging, metadata filtering and family-level
selection of the most recent source.
"""

from __future__ import annotations

import glob
import math
import os
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List

import yaml

_TOKEN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---[ \t]*\n?", re.DOTALL)
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
        ref = " - ".join(bits)
        if self.version or self.updated_at:
            version = self.version or "n/a"
            updated = self.updated_at or "n/a"
            ref += f" (version {version}, updated {updated})"
        return f"{ref}  [{self.source_id}]"


def _split_sections(body: str) -> List[tuple[str, str]]:
    """Split markdown into (heading, text) sections on headings."""
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
    """Parse one YAML front-matter block at the start of a file."""
    match = _FRONTMATTER_RE.match(raw)
    if not match:
        return {}, raw

    yaml_text = match.group(1)
    body = raw[match.end():].lstrip("\n")
    try:
        meta = yaml.safe_load(yaml_text) or {}
    except yaml.YAMLError:
        return {}, body
    if not isinstance(meta, dict):
        return {}, body
    return meta, body


def _parse_date(value: object) -> str:
    """Return an ISO date string or raise on invalid date metadata."""
    if value in (None, ""):
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    text = str(value).strip()
    if not text:
        return ""
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(
        f"Invalid date format: {text!r}. Expected ISO 8601, for example "
        "2024-01-15 or 2024-01-15T10:30:00Z."
    )


def load_corpus(corpus_dir: str) -> List[Chunk]:
    """Load every markdown document under `corpus_dir` into chunks."""
    chunks: List[Chunk] = []
    pattern = os.path.join(corpus_dir, "*.md")
    for path in sorted(glob.glob(pattern)):
        with open(path, encoding="utf-8") as fh:
            meta, body = _parse_frontmatter(fh.read())
        filename = os.path.splitext(os.path.basename(path))[0]
        source_id = str(meta.get("source_id") or filename)
        groups = meta.get("allowed_groups") or []
        if isinstance(groups, str):
            groups = [groups]
        updated_at = _parse_date(meta.get("updated_at"))
        for heading, text in _split_sections(body):
            title = str(meta.get("title") or source_id)
            token_text = f"{meta.get('title', '')} {heading} {text}"
            chunks.append(
                Chunk(
                    source_id=source_id,
                    title=title,
                    section=heading,
                    text=text,
                    version=str(meta.get("version") or ""),
                    updated_at=updated_at,
                    family=str(meta.get("family") or source_id),
                    allowed_groups=[str(g) for g in groups],
                    tokens=tokenize(token_text),
                )
            )
    return chunks


def _minmax(scores: Dict[int, float]) -> Dict[int, float]:
    if not scores:
        return {}
    lo, hi = min(scores.values()), max(scores.values())
    rng = hi - lo
    if rng < 1e-12:
        uniform = 1.0 / len(scores)
        return {k: uniform for k in scores}
    return {k: (v - lo) / rng for k, v in scores.items()}


@dataclass
class ScoredChunk:
    chunk: Chunk
    score: float


class HybridIndex:
    """BM25 and TF-IDF cosine over a fixed set of chunks."""

    def __init__(self, chunks: Sequence[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = list(chunks)
        self.k1 = k1
        self.b = b

    def _accessible(self, user_groups: Sequence[str]) -> List[int]:
        allowed = set(user_groups)
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
                numerator = f * (self.k1 + 1)
                denominator = f + self.k1 * (1 - self.b + self.b * dl / avgdl)
                s += idf * numerator / denominator
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

        if combined:
            floor = max(combined.values()) * min_ratio
            combined = {i: s for i, s in combined.items() if s >= floor}

        ranked = sorted(combined.items(), key=lambda kv: kv[1], reverse=True)

        family_pos: Dict[str, int] = {}
        order: List[int] = []
        for i, score in ranked:
            fam = self.chunks[i].family
            pos = family_pos.get(fam)
            if pos is None:
                family_pos[fam] = len(order)
                order.append(i)
                continue

            prev = order[pos]
            current_key = (self.chunks[i].updated_at, score)
            previous_key = (self.chunks[prev].updated_at, combined[prev])
            if current_key > previous_key:
                order[pos] = i

        return [ScoredChunk(self.chunks[i], combined[i]) for i in order[:top_k]]
