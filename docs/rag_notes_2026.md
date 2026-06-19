# RAG Notes 2026

## Purpose

These notes describe a practical baseline for Retrieval-Augmented Generation projects.

RAG helps an assistant answer from retrieved sources instead of relying only on model memory. A useful RAG setup depends on source quality, metadata, access rules, retrieval quality, prompt design and evaluation.

## Basic flow

1. Collect approved sources.
2. Clean and normalize documents.
3. Split documents into useful chunks.
4. Add metadata to every chunk.
5. Build a search index.
6. Retrieve candidate passages.
7. Rerank candidates.
8. Send the best context to the model.
9. Answer with source references.
10. Test with fixed questions.
11. Review feedback and failed answers.

## Recommended first setup

Start simple.

Use:

- hybrid retrieval: embeddings plus keyword search
- chunks around 300 to 800 tokens
- metadata per chunk
- access filtering before generation
- reranking for the strongest candidates
- source references in answers
- a fallback when sources are missing
- a fixed evaluation set

Do not start with GraphRAG, agents or complex multi-step retrieval unless the simple baseline clearly fails.

## Documents

Good document handling matters more than most model choices.

Track:

- title
- source system
- owner
- document type
- version
- created date
- updated date
- canonical URL
- access groups

Remove duplicates and mark outdated documents.

## Chunking

Good chunks contain one topic, enough local context and clear metadata.

Prefer structure-based chunking over blind token splitting. Split on headings, sections, paragraphs and tables where possible.

Add a short context header when a chunk would otherwise be unclear.

Example:

```text
Document: Product guide
Section: Warranty
Context: This passage explains warranty coverage and exceptions.
```

## Retrieval

Embeddings are useful for meaning. Keyword search is useful for exact terms, names, codes, dates and abbreviations.

A strong default is:

1. Run vector search.
2. Run keyword search.
3. Merge results.
4. Remove duplicates.
5. Rerank candidates.
6. Send only the strongest passages to the model.

## Answer generation

The model should answer only from the retrieved context.

The prompt should require the assistant to:

- cite used sources
- avoid unsupported claims
- state uncertainty
- name source conflicts
- say when the context is not enough
- keep answers short unless the user asks for detail

## Evaluation

Test retrieval and answer quality separately.

Check:

- whether the right source was found
- whether the right passage ranked high enough
- whether the answer matches the source
- whether citations support the answer
- whether missing context is handled well
- whether access rules are respected

Useful metrics:

- Recall@K
- MRR
- nDCG
- context precision
- context recall
- faithfulness
- answer relevancy
- citation accuracy

## Monitoring

Log enough information to debug quality problems:

- user question
- retrieved sources
- chunk scores
- rerank order
- answer
- cited sources
- feedback
- latency
- cost

## Maintenance

Assign owners for sources, prompts, config and evaluation data.

Update the evaluation set when source documents change or users ask new kinds of questions.

## Main rule

A RAG system is only as good as its sources, metadata, access rules and tests.
