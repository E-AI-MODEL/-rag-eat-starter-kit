# Recipes

Recipes are optional extension examples. They are not part of the dependency-free core path.

| Recipe | Purpose | Install |
|---|---|---|
| `chroma_multilingual.py` | Local multilingual vector retrieval with ChromaDB and sentence-transformers | `pip install -e ".[chroma]"` |
| `supabase_multiuser.py` | Multi-user retrieval with Supabase, pgvector and row-level security | `pip install -e ".[supabase]"` |

Keep these examples out of the default install. The base starter kit should still run with:

```bash
pip install -r requirements.txt
python3 run.py
```

Access filtering remains part of the retriever contract. A recipe must not return chunks whose `allowed_groups` do not overlap the caller's `user_groups`.
