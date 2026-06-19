# Project readiness checklist

Use this before putting a RAG assistant in front of users. For security and
access-control items, see `security/rag_security_checklist.md`.

## Sources

- [ ] Sources are approved for use.
- [ ] Each document has version and date metadata.
- [ ] Duplicates are removed and outdated documents are marked.

## Retrieval

- [ ] Hybrid retrieval (vector plus keyword) is configured.
- [ ] Reranking selects the strongest candidates.
- [ ] Chunking keeps one topic per chunk with useful metadata.

## Answers

- [ ] The assistant answers only from retrieved context.
- [ ] Answers cite their sources.
- [ ] There is a fallback when sources are insufficient.

## Evaluation and monitoring

- [ ] A fixed evaluation set exists and runs.
- [ ] Retrieval and answer quality are checked separately.
- [ ] Questions, sources, scores and feedback are logged.
