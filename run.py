#!/usr/bin/env python3
"""One command to drive the whole kit.

    python3 run.py                 # validate the EAT profile, then run the eval set
    python3 run.py validate        # validate the EAT profile only
    python3 run.py prompt          # print the system prompt rendered from the profile
    python3 run.py ask "question"  # ask the demo assistant a single question
    python3 run.py eval            # run the evaluation set and report pass/fail
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "src"))

from ragkit.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:], base_dir=ROOT))
