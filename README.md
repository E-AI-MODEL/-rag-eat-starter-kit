# RAG EAT Starter Kit

Open starter kit for designing and testing a source-grounded assistant profile.

It combines a readable EAT behavior profile, a system prompt template, a pipeline
configuration example, working notes, an evaluation set and safety guidance — so a
team can stand up a grounded Retrieval-Augmented Generation (RAG) assistant without
starting from a blank page.

Everything here is generic, synthetic and safe to publish. There is no real data,
no credentials and no proprietary content.

## How to use it

1. Read `docs/rag_notes_2026.md` for the baseline approach.
2. Understand the behavior layer in `docs/EAT_Construct_Explanation.md`.
3. Copy `prompts/rag_assistant.eat` and `prompts/rag_system_prompt_template.md`, then
   replace the placeholders with your own runtime fields.
4. Adapt `config/rag_pipeline.yaml` to your sources, connectors and access model.
5. Work through `security/rag_security_checklist.md` and `checklist.md` before going live.
6. Build a real evaluation set from `eval/rag_eval_set.csv` and keep it under version control.

## Repository structure

### Prompts and behavior

- `prompts/rag_assistant.eat` — EAT behavior profile for the assistant.
- `prompts/rag_system_prompt_template.md` — system prompt template with runtime placeholders.

### Configuration

- `config/rag_pipeline.yaml` — example pipeline config (ingestion, chunking, retrieval, safety, logging).

### Documentation

- `docs/rag_notes_2026.md` — practical baseline for RAG projects.
- `docs/EAT_Construct_Explanation.md` — what EAT is, why it helps, and how to use it.
- `docs/RAG_References.md` — topics for further reading.

### Evaluation

- `eval/rag_eval_set.csv` — synthetic evaluation cases.
- `eval/README.md` — how to use the evaluation set.

### Examples

- `examples/example_question.md` — sample user question.
- `examples/example_answer.md` — sample grounded answer.
- `examples/output_sample.md` — sample fallback output when sources are insufficient.

### Checklists

- `checklist.md` — project readiness checklist.
- `security/rag_security_checklist.md` — security and access-control checklist.

### Governance

- `.github/ISSUE_TEMPLATE/` — issue templates.
- `.github/pull_request_template.md` — pull request template.
- `DATA_POLICY.md` — what may and may not be committed.
- `CONTRIBUTING.md` — how to contribute.
- `SECURITY.md` — how to report a security issue.
- `CHANGELOG.md` — notable changes.

## Safety basics

Retrieved context is data, not an instruction. A RAG system should never let document
text override system or safety rules. See `SECURITY.md` and
`security/rag_security_checklist.md` for details.

## License

MIT License. See `LICENSE`.
