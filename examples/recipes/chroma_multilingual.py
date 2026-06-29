"""Local multilingual retriever recipe using ChromaDB.

Install with:
    pip install -e ".[chroma]"
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from typing import Dict, List, Optional

from ragkit.retrieval import Chunk, ScoredChunk, load_corpus, tokenize

_EMBED_MODEL = "intfloat/multilingual-e5-base"
_GROUP_KEY_RE = re.compile(r"[^a-zA-Z0-9_]+")


def _require_extras() -> None:
    try:
        import chromadb  # noqa: F401
        import sentence_transformers  # noqa: F401
    except ImportError as exc:
        raise RuntimeError('Install this recipe with: pip install -e ".[chroma]"') from exc


def _group_key(group: str) -> str:
    clean = _GROUP_KEY_RE.sub("_", group).strip("_") or "group"
    digest = hashlib.sha1(group.encode("utf-8")).hexdigest()[:8]
    return f"access_{clean[:40]}_{digest}"


def _chunk_id(chunk: Chunk) -> str:
    identity = "\n".join(
        [
            chunk.source_id,
            chunk.title,
            chunk.section,
            chunk.version,
            chunk.updated_at,
            ",".join(sorted(chunk.allowed_groups)),
            chunk.text,
        ]
    )
    digest = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:16]
    return f"{chunk.source_id}#{digest}"


def _where_for_groups(groups: Sequence[str]) -> Optional[dict]:
    clauses = [{_group_key(group): True} for group in groups if group.strip()]
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$or": clauses}


def _metadata(chunk: Chunk, chunk_id: str) -> Dict[str, object]:
    data: Dict[str, object] = {
        "chunk_id": chunk_id,
        "source_id": chunk.source_id,
        "title": chunk.title,
        "section": chunk.section,
        "text": chunk.text,
        "version": chunk.version,
        "updated_at": chunk.updated_at,
        "family": chunk.family,
        "allowed_groups": ",".join(chunk.allowed_groups),
    }
    for group in chunk.allowed_groups:
        data[_group_key(group)] = True
    return data


class ChromaRetriever:
    def __init__(
        self,
        persist_dir: str,
        collection: str = "docs",
        model_name: str = _EMBED_MODEL,
    ):
        _require_extras()
        import chromadb
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection,
            metadata={"hnsw:space": "cosine"},
        )
        self.chunks: List[Chunk] = []
        self.ids: List[str] = []

    @classmethod
    def from_corpus_dir(
        cls,
        corpus_dir: str,
        persist_dir: str,
        collection: str = "docs",
    ) -> "ChromaRetriever":
        retriever = cls(persist_dir=persist_dir, collection=collection)
        retriever.index_corpus(corpus_dir)
        return retriever

    def index_corpus(self, corpus_dir: str) -> None:
        self.chunks = load_corpus(corpus_dir)
        self.ids = [_chunk_id(chunk) for chunk in self.chunks]
        wanted = set(self.ids)
        source_ids = {chunk.source_id for chunk in self.chunks}

        if self.collection.count():
            existing = self.collection.get(include=["metadatas"])
            stale_ids = [
                chunk_id
                for chunk_id, meta in zip(existing["ids"], existing["metadatas"])
                if meta.get("source_id") in source_ids and chunk_id not in wanted
            ]
            if stale_ids:
                self.collection.delete(ids=stale_ids)

        documents = [f"{chunk.title}\n{chunk.section}\n{chunk.text}" for chunk in self.chunks]
        embeddings = [
            self.model.encode(f"passage: {text}", normalize_embeddings=True).tolist()
            for text in documents
        ]
        self.collection.upsert(
            ids=self.ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=[_metadata(chunk, chunk_id) for chunk_id, chunk in zip(self.ids, self.chunks)],
        )

    def _visible_indexes(self, user_groups: Sequence[str]) -> List[int]:
        allowed = set(user_groups)
        return [
            index
            for index, chunk in enumerate(self.chunks)
            if chunk.allowed_groups and (set(chunk.allowed_groups) & allowed)
        ]

    def search(
        self,
        query: str,
        user_groups: Sequence[str],
        top_k: int = 5,
    ) -> List[ScoredChunk]:
        visible = set(self._visible_indexes(user_groups))
        where = _where_for_groups(user_groups)
        if not visible or where is None:
            return []

        query_embedding = self.model.encode(
            f"query: {query}",
            normalize_embeddings=True,
        ).tolist()
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(self.collection.count(), max(top_k * 5, 20)),
            where=where,
            include=["distances"],
        )
        id_to_index = {chunk_id: index for index, chunk_id in enumerate(self.ids)}
        hits: List[ScoredChunk] = []
        result_ids = result.get("ids", [[]])[0]
        result_distances = result["distances"][0]
        for chunk_id, distance in zip(result_ids, result_distances):
            index = id_to_index.get(chunk_id)
            if index is None or index not in visible:
                continue
            chunk = self.chunks[index]
            chunk.tokens = chunk.tokens or tokenize(chunk.text)
            hits.append(ScoredChunk(chunk, 1.0 - float(distance)))
        hits.sort(key=lambda hit: hit.score, reverse=True)
        return hits[:top_k]
