# Getting started — a guided walkthrough

This walkthrough takes about ten minutes. By the end you will have run a real
source-grounded assistant, seen it cite sources, watched it refuse to answer when it
should, and proven the same with an evaluation set. No API keys are required.

## 0. Prerequisites

- Python 3.9 or newer
- `pip install -r requirements.txt` (only PyYAML)

```bash
pip install -r requirements.txt
```

## 1. Validate the behavior profile

The assistant's behavior lives in one file: `prompts/rag_assistant.eat`. It is not a
loose prompt string — it is validated. Run:

```bash
python3 run.py validate
```

You should see the identity, the number of workflow steps, the number of rules, and
`locked: True`. If you break the profile — say, change `workflow[7]` to `workflow[6]`
without removing a row — validation fails loudly. That is the point: behavior is
reviewable and cannot silently drift.

## 2. See the system prompt it produces

```bash
python3 run.py prompt
```

This is the actual system prompt the assistant runs with, rendered from the EAT
profile. Notice the mission, the numbered workflow, and the rules that outrank
retrieved content. Change the `.eat` file, re-run, and the prompt changes with it.

## 3. Ask a question that has an answer

```bash
python3 run.py ask "What are the cancellation conditions?"
```

The assistant retrieves from the demo corpus (`examples/corpus/`), answers from that
context, and cites the exact source and section. The answer is grounded — it does not
come from model memory.

## 4. Ask a question it must refuse

```bash
python3 run.py ask "What is the internal pricing markup?"
```

That information exists in the corpus (`internal_pricing.md`), but it is tagged
`allowed_groups: [finance]`, and the demo user is only in `public`/`support`. The
document is filtered out **before** generation, so the assistant abstains. This is
fail-closed access control: a source the user may not see can never leak into an answer.

Try the same question as a finance user and it works:

```python
# in a Python shell
from run import _build_assistant  # demo user is public/support
```

(or change `DEMO_USER_GROUPS` in `run.py` to `["finance"]` and re-run step 4.)

## 5. Run the evaluation set

```bash
python3 run.py eval
```

This runs every case in `eval/rag_eval_set.csv` against the real assistant and reports
pass/fail: source lookups, exact-term retrieval, "prefer the latest version", access
control, and refusal when no source supports the question. The command exits non-zero
if any case fails, so it works in CI.

## 6. Run the tests

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

These assert the claims hold: the EAT validator rejects malformed profiles, access
control hides finance documents from non-finance users (and shows them to finance
users), retrieval prefers the latest version, and the assistant abstains without support.

## 7. Make it yours

- **Your documents:** drop Markdown files into `examples/corpus/` (see its README for
  the front-matter fields). Set `allowed_groups` honestly.
- **Your behavior:** edit `prompts/rag_assistant.eat`. Keep `workflow[n]` in sync with
  the number of steps; validation will tell you if you forget.
- **Your tests:** add rows to `eval/rag_eval_set.csv`.
- **A real model:** by default answers are extractive so the demo runs offline. To use
  an LLM, pass an `llm=` callable to `ragkit.Assistant` — see the README section
  "Plug in a real model".

That is the whole loop: a validated behavior profile, grounded retrieval with
access control, and an evaluation set that proves it — all runnable on your machine.
