"""Multi-user retriever recipe using Supabase, Postgres and pgvector.

Install with:
    pip install -e ".[supabase]"

The read path expects a user-scoped JWT. Keep privileged project keys for backend
write jobs only.
"""

from __future__ import annotations

import base64
import json
from collections.abc import Sequence
from typing import Any, Dict, List, Optional

from ragkit.retrieval import Chunk, ScoredChunk, tokenize

_EMBED_MODEL = "intfloat/multilingual-e5-base"
_OPAQUE_PRIVILEGED_PREFIXES = ("sb_secret_",)


def _require_extras() -> None:
    try:
        import sentence_transformers  # noqa: F401
        import supabase  # noqa: F401
    except ImportError as exc:
        raise RuntimeError('Install this recipe with: pip install -e ".[supabase]"') from exc


def _jwt_payload(token: str) -> Optional[Dict[str, Any]]:
    parts = token.split(".")
    if len(parts) < 2:
        return None
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(payload.encode("ascii")))
    except (ValueError, UnicodeDecodeError):
        return None


def _jwt_role(token: str) -> Optional[str]:
    payload = _jwt_payload(token)
    if not payload:
        return None
    role = payload.get("role")
    return str(role) if role else None


def _require_user_jwt(key: str) -> None:
    if key.startswith(_OPAQUE_PRIVILEGED_PREFIXES):
        raise ValueError("SupabaseRetriever reads require a user JWT, not an opaque project key.")
    payload = _jwt_payload(key)
    if payload is None or not payload.get("sub"):
        raise ValueError("SupabaseRetriever reads require a user-scoped JWT.")
    if payload.get("role") == "service_role":
        raise ValueError("SupabaseRetriever reads require a user JWT, not a privileged JWT.")


def _require_backend_write_key(key: str) -> None:
    if key.startswith(_OPAQUE_PRIVILEGED_PREFIXES):
        return
    if _jwt_role(key) != "service_role":
        raise ValueError("insert_document must run with a backend write key.")


class SupabaseRetriever:
    def __init__(
        self,
        url: str,
        key: str,
        user_id: str,
        model_name: str = _EMBED_MODEL,
    ):
        _require_extras()
        from sentence_transformers import SentenceTransformer
        from supabase import create_client

        if not url or not key or not user_id:
            raise ValueError("url, key and user_id are required.")
        _require_user_jwt(key)

        self.user_id = user_id
        self.client = create_client(url, key)
        self.model = SentenceTransformer(model_name)

    def _embed_query(self, query: str) -> List[float]:
        return self.model.encode(f"query: {query}", normalize_embeddings=True).tolist()

    def _row_to_chunk(self, row: Dict[str, Any]) -> Chunk:
        body = str(row.get("body") or "")
        token_text = f"{row.get('title', '')} {row.get('section', '')} {body}"
        return Chunk(
            source_id=str(row["source_id"]),
            title=str(row.get("title") or row["source_id"]),
            section=str(row.get("section") or ""),
            text=body,
            version=str(row.get("version") or ""),
            updated_at=str(row.get("updated_at") or ""),
            family=str(row.get("family") or row["source_id"]),
            allowed_groups=list(row.get("allowed_groups") or []),
            tokens=tokenize(token_text),
        )

    def search(
        self,
        query: str,
        user_groups: Sequence[str],
        top_k: int = 5,
    ) -> List[ScoredChunk]:
        groups = [group for group in user_groups if group.strip()]
        if not groups:
            return []
        payload = {
            "query_embedding": self._embed_query(query),
            "match_user_id": self.user_id,
            "match_groups": groups,
            "match_count": max(top_k * 3, 15),
        }
        response = self.client.rpc("match_documents", payload).execute()
        allowed = set(groups)
        hits: List[ScoredChunk] = []
        for row in response.data or []:
            chunk = self._row_to_chunk(row)
            if not chunk.allowed_groups or not (set(chunk.allowed_groups) & allowed):
                continue
            score = float(row.get("similarity") or 0.0)
            hits.append(ScoredChunk(chunk, score))
        hits.sort(key=lambda hit: hit.score, reverse=True)
        return hits[:top_k]


def insert_document(
    url: str,
    service_key: str,
    user_id: str,
    source_id: str,
    body: str,
    *,
    title: Optional[str] = None,
    section: str = "",
    allowed_groups: Optional[List[str]] = None,
    family: Optional[str] = None,
    version: str = "1.0",
    updated_at: str = "",
    model_name: str = _EMBED_MODEL,
) -> None:
    _require_extras()
    _require_backend_write_key(service_key)
    from sentence_transformers import SentenceTransformer
    from supabase import create_client

    model = SentenceTransformer(model_name)
    embedding = model.encode(f"passage: {body}", normalize_embeddings=True).tolist()
    row = {
        "user_id": user_id,
        "source_id": source_id,
        "title": title or source_id,
        "section": section,
        "body": body,
        "allowed_groups": allowed_groups or ["public"],
        "family": family or source_id,
        "version": version,
        "updated_at": updated_at,
        "embedding": embedding,
    }
    create_client(url, service_key).table("documents").insert(row).execute()
