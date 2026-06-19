"""Command-line entry point for the kit.

    rag-eat                 # validate the EAT profile, then run the eval set
    rag-eat validate        # validate the EAT profile only
    rag-eat prompt          # print the system prompt rendered from the EAT profile
    rag-eat ask "question"  # ask the demo assistant a single question
    rag-eat eval            # run the evaluation set and report pass/fail

Paths are resolved relative to the current working directory (run from the repo
root), or override them with the RAGKIT_EAT / RAGKIT_CORPUS / RAGKIT_EVAL env vars.
"""

from __future__ import annotations

import os
import sys

from .assistant import Assistant
from .eat_loader import load_eat
from .eval_runner import format_report, run_eval
from .retrieval import HybridIndex, load_corpus

# The demo user belongs to "public" and "support" — but NOT "finance".
# That is what makes the access-control eval case meaningful.
DEMO_USER_GROUPS = ["public", "support"]


def _paths(base_dir: str) -> tuple[str, str, str]:
    eat = os.environ.get("RAGKIT_EAT", os.path.join(base_dir, "prompts", "rag_assistant.eat"))
    corpus = os.environ.get("RAGKIT_CORPUS", os.path.join(base_dir, "examples", "corpus"))
    csv = os.environ.get("RAGKIT_EVAL", os.path.join(base_dir, "eval", "rag_eval_set.csv"))
    return eat, corpus, csv


def _build_assistant(base_dir: str) -> Assistant:
    eat, corpus, _ = _paths(base_dir)
    profile = load_eat(eat)  # raises EATValidationError if malformed
    index = HybridIndex(load_corpus(corpus))
    return Assistant(profile, index, DEMO_USER_GROUPS)


def cmd_validate(base_dir: str) -> int:
    eat, _, _ = _paths(base_dir)
    profile = load_eat(eat)
    print(f"EAT profile OK: {eat}")
    print(f"  identity : {', '.join(profile.simple('identity'))}")
    print(f"  workflow : {len(profile.table('workflow'))} steps")
    print(f"  rules    : {len(profile.simple('rules'))}")
    print(f"  locked   : {profile.locked}")
    return 0


def cmd_prompt(base_dir: str) -> int:
    eat, _, _ = _paths(base_dir)
    print(load_eat(eat).render_system_prompt())
    return 0


def cmd_ask(base_dir: str, question: str) -> int:
    res = _build_assistant(base_dir).answer(question)
    print(res.answer)
    if res.abstained:
        print("\n(assistant abstained: no supporting, accessible source)")
    return 0


def cmd_eval(base_dir: str) -> int:
    _, _, csv = _paths(base_dir)
    results = run_eval(_build_assistant(base_dir), csv)
    print(format_report(results))
    return 0 if all(r.passed for r in results) else 1


def main(argv: list[str] | None = None, base_dir: str | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    base_dir = base_dir or os.getcwd()
    cmd = argv[0] if argv else "all"

    eat, _, _ = _paths(base_dir)
    if cmd in {"validate", "prompt", "ask", "eval", "all"} and not os.path.exists(eat):
        print(
            f"Could not find the EAT profile at {eat}.\n"
            "Run this from the repository root, or set RAGKIT_EAT / RAGKIT_CORPUS / "
            "RAGKIT_EVAL to point at your files.",
            file=sys.stderr,
        )
        return 2

    if cmd == "validate":
        return cmd_validate(base_dir)
    if cmd == "prompt":
        return cmd_prompt(base_dir)
    if cmd == "ask":
        if len(argv) < 2:
            print('usage: rag-eat ask "your question"', file=sys.stderr)
            return 2
        return cmd_ask(base_dir, argv[1])
    if cmd == "eval":
        return cmd_eval(base_dir)
    if cmd == "all":
        rc = cmd_validate(base_dir)
        if rc != 0:
            return rc
        print()
        return cmd_eval(base_dir)

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
