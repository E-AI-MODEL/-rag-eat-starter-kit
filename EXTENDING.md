# Extending the kit

The base kit stays small. This guide shows the supported extension points.

## Retriever protocol

`src/ragkit/retriever.py` defines a small protocol:

```python
def search(query: str, user_groups: Sequence[str], top_k: int = 5) -> List[ScoredChunk]:
    ...
```

Any object with that method can be passed to `Assistant`. The built-in
`HybridIndex` already matches it.

A retriever should return results for the caller's groups only. Use the
`allowed_groups` metadata on each chunk to decide what can be returned.

## Chroma recipe

Use `examples/recipes/chroma_multilingual.py` for local multilingual retrieval.

```bash
pip install -e ".[chroma]"
```

```python
from ragkit import Assistant, load_eat
from examples.recipes.chroma_multilingual import ChromaRetriever

retriever = ChromaRetriever.from_corpus_dir("examples/corpus", "./chroma_db")
assistant = Assistant(load_eat("prompts/rag_assistant.eat"), retriever, ["public"])
```

## Supabase recipe

Use `examples/recipes/supabase_multiuser.py` for a hosted Postgres plus pgvector
setup.

```bash
pip install -e ".[supabase]"
```

The recipe calls a Postgres RPC named `match_documents`. That RPC should accept
query embedding, user id, groups and result count, then return matching rows in
score order.

## Fork guidance

Keep project-specific APIs, deployment files and corpora in a fork. Send small
bug fixes, tests and docs back upstream.
