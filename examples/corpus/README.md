# Demo corpus

This folder is a tiny, fully synthetic knowledge base used by the runnable demo
(`run.py`) and the tests. Nothing here is real data.

Each document is a Markdown file with a YAML front-matter header. The header carries
the same metadata the pipeline config (`config/rag_pipeline.yaml`) marks as required —
this is where access control and "prefer the latest source" actually come from.

```markdown
---
source_id: cancellation_terms      # stable id used in citations
title: Cancellation Terms          # human title (shown in citations)
family: product_guide              # optional: group versions of the "same" doc
document_type: policy
version: "2.0"
created_at: "2026-01-10"
updated_at: "2026-05-01"           # newest in a family wins
owner: support_team
allowed_groups: [public, support]  # ACCESS CONTROL — fail-closed
canonical_url: https://example.com/terms/cancellation
---

# Heading
Body text. The loader splits a document into one chunk per `#` heading.
```

## What each document demonstrates

| File | Demonstrates |
|---|---|
| `cancellation_terms.md` | a normal source lookup with citation |
| `warranty_policy.md` | citation quality (answer points at the right section) |
| `product_codes.md` | exact-term retrieval (BM25 finds code `X-123`) |
| `product_guide_v1.md` / `product_guide_v2.md` | "prefer the latest source" via `family` + `updated_at` |
| `internal_pricing.md` | fail-closed access control (`allowed_groups: [finance]`) |

## Use your own documents

Drop your own `*.md` files here (or point `CORPUS_DIR` in `run.py` at another folder),
keep the front-matter fields above, and the demo will index them. Set `allowed_groups`
honestly: a document with no groups, or no overlap with the user's groups, is never
retrieved and can never appear in an answer.
