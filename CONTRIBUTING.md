# Contributing

Thanks for contributing.

## Guidelines

- Keep examples generic and safe.
- Do not add real personal data.
- Do not add secrets.
- Write clearly and practically.
- Add a short example for new concepts.
- Keep evaluation examples synthetic or anonymized.
- Add sources when they are needed.

## Ways to contribute

You can help with:

- better RAG checklists
- extra evaluation cases
- clearer prompt rules
- examples of retrieval problems
- safety tests
- EAT documentation
- translations

## Pull requests

Describe:

1. What you changed.
2. Why it helps.
3. Whether it affects prompts, config or evaluation.
4. Whether you checked for sensitive data.

## Releasing

Releases are cut from `main` once CI is green:

1. Move the relevant items from `## [Unreleased]` in `CHANGELOG.md` into a new
   `## [x.y.z] - YYYY-MM-DD` section, and bump `version` in `pyproject.toml`.
2. Run the **Release** workflow (Actions → Release → Run workflow) with the tag
   `vX.Y.Z`. It re-runs the tests, creates the git tag, and publishes a GitHub Release
   with notes taken from the matching `CHANGELOG.md` section.

Pushing a `vX.Y.Z` tag also triggers the same workflow.
