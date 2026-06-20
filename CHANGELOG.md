# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project uses semantic versioning.

## [Unreleased]

## [0.1.0] - 2026-06-20

### Added
- Initial public release of the RAG EAT Starter Kit.
- **Runnable core** (`src/ragkit/`): `run.py` validates the EAT profile and drives a
  real RAG loop — EAT-rendered system prompt, hybrid retrieval (BM25 + TF-IDF),
  fail-closed access control, and grounded answering with abstention.
- EAT loader/validator that enforces the EAT-Core grammar (header forms, exact `[n]`
  row counts, identifier cells, required blocks) and renders the system prompt.
- Synthetic demo corpus under `examples/corpus/` with access metadata.
- Executable evaluation: `eval/rag_eval_set.csv` is run against the assistant and
  scored (`src/ragkit/eval_runner.py`); cases map to the demo corpus.
- Packaging (`pyproject.toml`): pip-installable, with a `rag-eat` console script,
  `ruff` lint config, and a `dev` extra.
- A worked, runnable LLM adapter (`examples/llm_anthropic_adapter.py`) for plugging a
  real model into the vendor-neutral `Assistant`.
- Unit tests (`tests/`), `Makefile`, a matrix GitHub Actions CI (`ruff` + tests across
  Python 3.9–3.12), README status badges, and a guided walkthrough
  (`docs/GETTING_STARTED.md`).
- Release automation (`.github/workflows/release.yml`) that re-runs the tests, creates
  the git tag, and publishes a GitHub Release with notes drawn from this changelog.

### Changed
- Translated the system prompt template and reference list to English so the kit is
  English-only.
- Rewrote the README around the runnable demo, with an architecture diagram, a command
  table, and instructions to plug in a real model and your own documents.
- Expanded `checklist.md` into a project readiness checklist that complements the
  security checklist, and `examples/output_sample.md` with a concrete fallback example.

### Fixed
- Linked `security/rag_security_checklist.md` from the README.
