# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project uses semantic versioning.

## [Unreleased]

### Added
- Packaging (`pyproject.toml`): the kit is pip-installable (`pip install -e .`) and
  exposes a `rag-eat` console script; `ruff` lint config and a `dev` extra.
- A worked, runnable LLM adapter (`examples/llm_anthropic_adapter.py`) showing how to
  plug a real model into the vendor-neutral `Assistant`.
- README status badges (CI, Python, license); CI now also lints with `ruff` and
  installs the package editable.
- **Runnable core** (`src/ragkit/`): the kit now runs. `run.py` validates the EAT
  profile and drives a real RAG loop — EAT-rendered system prompt, hybrid retrieval
  (BM25 + TF-IDF), fail-closed access control, grounded answering with abstention.
- EAT loader/validator that enforces the EAT-Core grammar (header forms, exact `[n]`
  row counts, identifier cells) and renders the system prompt.
- Synthetic demo corpus under `examples/corpus/` with access metadata.
- Executable evaluation: `eval/rag_eval_set.csv` is now run against the assistant and
  scored (`src/ragkit/eval_runner.py`); cases map to the demo corpus.
- Unit tests (`tests/`), `requirements.txt`, `Makefile`, GitHub Actions CI, and a
  guided walkthrough (`docs/GETTING_STARTED.md`).

### Changed
- Translated `prompts/rag_system_prompt_template.md` and `docs/RAG_References.md` to
  English so the kit is English-only.
- Rewrote the README around the runnable demo, with an architecture overview, a command
  table, and instructions to plug in a real model and your own documents.
- Expanded `checklist.md` into a project readiness checklist that complements the
  security checklist.
- Expanded `examples/output_sample.md` with a concrete fallback output example.

### Fixed
- Linked `security/rag_security_checklist.md` from the README.

## [0.1.0]

### Added
- Initial public release: EAT behavior profile, system prompt template, pipeline
  configuration, RAG notes, evaluation set, examples, checklists and governance docs.
