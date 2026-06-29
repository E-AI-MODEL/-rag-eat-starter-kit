# Extending the kit

This guide covers the supported extension points for users who outgrow the small
local demo. The default path remains unchanged:

```bash
pip install -r requirements.txt
python3 run.py
```

Optional recipes live under `examples/recipes/`. They are examples, not required
core dependencies.

## Retriever protocol

`src/ragkit/retriever.py` defines the retrieval extension point:

```python
class Retriever(Protocol):
    def search(self, query: str, user_groups: Sequence[str], top_k: int = 5) -> List[ScoredChunk]: ...
```

Any object with that `search` method can be passed to `Assistant`. `HybridIndex`
still satisfies this protocol, so existing code keeps working.

The hard rule is access control: a retriever must not return chunks whose
`allowed_groups` do not overlap `user_groups`. Filter in the backend when the
backend supports it, and re-check before returning `ScoredChunk` values.

## Chroma recipe

Use this when you want local multilingual vector retrieval.

```bash
pip install -e ".[chroma]"
```

```python
from ragkit import Assistant, load_eat
from examples.recipes.chroma_multilingual import ChromaRetriever

retriever = ChromaRetriever.from_corpus_dir(
    corpus_dir="examples/corpus",
    persist_dir="./chroma_db",
    collection="docs",
)
assistant = Assistant(
    load_eat("prompts/rag_assistant.eat"),
    retriever,
    user_groups=["public", "support"],
)
print(assistant.answer("Wat zijn de annuleringsvoorwaarden?").answer)
```

The recipe uses `intfloat/multilingual-e5-base`, persistent Chroma storage,
metadata filters for access groups, and a unique ID per chunk. The unique chunk
ID matters: documents can have multiple sections, and matching only on
`source_id` can return the wrong section.

The Chroma recipe is intentionally not part of CI because it downloads model and
vector-store dependencies. The core repo still runs without it.

## Supabase recipe

Use this when you want per-user document storage with Postgres, pgvector and
row-level security.

```bash
pip install -e ".[supabase]"
```

Read path rule: use a user-scoped JWT, not the Supabase service-role key. The
service-role key bypasses row-level security and belongs only in trusted backend
write jobs.

### Schema

Run this in the Supabase SQL editor:

```sql
create extension if not exists vector;

create table documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  source_id text not null,
  title text,
  section text,
  body text not null,
  allowed_groups text[] not null default '{}',
  family text,
  version text,
  updated_at date,
  embedding vector(768)
);

alter table documents enable row level security;

create policy "users see own docs" on documents
  for select using (auth.uid() = user_id);

create index documents_embedding_idx
  on documents using ivfflat (embedding vector_cosine_ops);
```

### RPC

The retriever calls `match_documents`. The function receives the authenticated
user id and access groups explicitly. RLS still applies because the function is
not `security definer`.

```sql
create or replace function match_documents(
  query_embedding vector(768),
  match_user_id uuid,
  match_groups text[],
  match_count int
)
returns table(
  id uuid,
  user_id uuid,
  source_id text,
  title text,
  section text,
  body text,
  allowed_groups text[],
  family text,
  version text,
  updated_at date,
  similarity float
)
language sql stable
as $$
  select
    d.id,
    d.user_id,
    d.source_id,
    d.title,
    d.section,
    d.body,
    d.allowed_groups,
    d.family,
    d.version,
    d.updated_at,
    1 - (d.embedding <=> query_embedding) as similarity
  from documents d
  where d.user_id = match_user_id
    and d.allowed_groups && match_groups
  order by d.embedding <=> query_embedding
  limit match_count;
$$;
```

Use it like this:

```python
import os
from ragkit import Assistant, load_eat
from examples.recipes.supabase_multiuser import SupabaseRetriever

retriever = SupabaseRetriever(
    url=os.environ["SUPABASE_URL"],
    key=os.environ["SUPABASE_USER_JWT"],
    user_id=current_user_id,
)
assistant = Assistant(
    load_eat("prompts/rag_assistant.eat"),
    retriever,
    user_groups=["public"],
)
```

The Python code performs a second access check before returning results. That is
defense in depth, not a replacement for the SQL filter and RLS.

## LLM callable

The answer step can use any model provider by passing `llm=` to `Assistant`:

```python
def my_llm(system_prompt: str, question: str, context: list[str]) -> str:
    ...
```

Retrieval and access filtering run before the callable is invoked, so the model
only receives allowed context.

## Forking

Use a fork for project-specific retrievers, auth, deployment config or private
prompts. Keep your fork synced with upstream before opening PRs back here:

```bash
git remote add upstream https://github.com/E-AI-MODEL/-rag-eat-starter-kit.git
git fetch upstream
git checkout main
git pull upstream main
git push origin main
```

For feature work, branch from the synced `main`:

```bash
git checkout -b my-change
```

## What belongs upstream

Good upstream PRs keep the small local path clean: bugfixes, tests, docs, safety
checks, and small protocol improvements. Project-specific retrievers, auth,
deployment config and proprietary prompts usually belong in a fork or an
optional recipe.
