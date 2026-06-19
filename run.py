#!/usr/bin/env python3
"""One command to drive the whole kit.

    python3 run.py                 # validate the EAT profile, then run the eval set
    python3 run.py validate        # validate the EAT profile only
    python3 run.py prompt          # print the system prompt rendered from the EAT profile
    python3 run.py ask "question"  # ask the demo assistant a single question
    python3 run.py eval            # run the evaluation set and report pass/fail

Everything runs locally, offline, with no API keys. To use a real LLM, see the
`llm=` parameter of `ragkit.Assistant` and the README "Plug in a model" section.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ragkit import HybridIndex, load_corpus, load_eat  # noqa: E402
from ragkit.assistant import Assistant  # noqa: E402
from ragkit.eval_runner import format_report, run_eval  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
EAT_PATH = os.path.join(ROOT, "prompts", "rag_assistant.eat")
CORPUS_DIR = os.path.join(ROOT, "examples", "corpus")
EVAL_CSV = os.path.join(ROOT, "eval", "rag_eval_set.csv")

# The demo user belongs to "public" and "support" — but NOT "finance".
# That is what makes the access-control eval case meaningful.
DEMO_USER_GROUPS = ["public", "support"]


def _build_assistant() -> Assistant:
    profile = load_eat(EAT_PATH)  # raises EATValidationError if malformed
    index = HybridIndex(load_corpus(CORPUS_DIR))
    return Assistant(profile, index, DEMO_USER_GROUPS)


def cmd_validate() -> int:
    profile = load_eat(EAT_PATH)
    wf = profile.table("workflow")
    print(f"EAT profile OK: {EAT_PATH}")
    print(f"  identity : {', '.join(profile.simple('identity'))}")
    print(f"  workflow : {len(wf)} steps")
    print(f"  rules    : {len(profile.simple('rules'))}")
    print(f"  locked   : {profile.locked}")
    return 0


def cmd_prompt() -> int:
    print(load_eat(EAT_PATH).render_system_prompt())
    return 0


def cmd_ask(question: str) -> int:
    res = _build_assistant().answer(question)
    print(res.answer)
    if res.abstained:
        print("\n(assistant abstained: no supporting, accessible source)")
    return 0


def cmd_eval() -> int:
    results = run_eval(_build_assistant(), EVAL_CSV)
    print(format_report(results))
    return 0 if all(r.passed for r in results) else 1


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "all"
    if cmd == "validate":
        return cmd_validate()
    if cmd == "prompt":
        return cmd_prompt()
    if cmd == "ask":
        if len(argv) < 2:
            print('usage: python3 run.py ask "your question"', file=sys.stderr)
            return 2
        return cmd_ask(argv[1])
    if cmd == "eval":
        return cmd_eval()
    if cmd == "all":
        rc = cmd_validate()
        print()
        return cmd_eval() or rc
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
