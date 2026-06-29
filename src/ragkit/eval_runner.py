"""Run `eval/rag_eval_set.csv` against the assistant and report pass/fail.

This turns the evaluation set from an aspiration into a check that actually runs.
Each row's `pass_condition` is evaluated against the assistant's real output:

- cites_expected_source              -> answered and cited the expected source_id
- cites_latest_with_version_and_date -> cited the latest source in a family
- abstains                           -> assistant refused because no source supports it
- abstains_and_no_leak               -> refused and did not cite the restricted source
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from typing import List

from .assistant import AnswerResult, Assistant

_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_VERSION = re.compile(r"version\s+[0-9]", re.IGNORECASE)


@dataclass
class CaseResult:
    id: str
    category: str
    question: str
    passed: bool
    detail: str


def _latest_family_member(assistant: Assistant, family: str) -> str:
    chunks = getattr(assistant.index, "chunks", None)
    if chunks is None:
        return ""
    members = [c for c in chunks if c.family == family]
    if not members:
        return ""
    return max(members, key=lambda c: c.updated_at).source_id


def _check(assistant: Assistant, row: dict, res: AnswerResult) -> tuple[bool, str]:
    cond = row["pass_condition"].strip()
    expected = row["expected_source"].strip()

    if cond == "cites_expected_source":
        ok = (not res.abstained) and expected in res.cited_sources
        return ok, f"cited={res.cited_sources}"

    if cond == "cites_latest_with_version_and_date":
        latest = _latest_family_member(assistant, expected)
        has_version_and_date = bool(_VERSION.search(res.answer)) and bool(_DATE.search(res.answer))
        if latest:
            ok = (not res.abstained) and latest in res.cited_sources and has_version_and_date
            return ok, f"latest={latest} cited={res.cited_sources}"

        # Custom retrievers may not expose their full corpus as `.chunks`. In
        # that case, check the family cited by the returned chunk instead.
        ok = (not res.abstained) and expected in res.cited_families and has_version_and_date
        return ok, f"latest=unavailable cited_families={res.cited_families}"

    if cond == "abstains":
        return res.abstained, f"abstained={res.abstained}"

    if cond == "abstains_and_no_leak":
        ok = res.abstained and expected not in res.cited_sources
        return ok, f"abstained={res.abstained} cited={res.cited_sources}"

    return False, f"unknown pass_condition: {cond!r}"


def run_eval(assistant: Assistant, csv_path: str) -> List[CaseResult]:
    results: List[CaseResult] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            res = assistant.answer(row["question"])
            ok, detail = _check(assistant, row, res)
            results.append(
                CaseResult(row["id"], row["category"], row["question"], ok, detail)
            )
    return results


def format_report(results: List[CaseResult]) -> str:
    lines = ["", "RAG evaluation", "=" * 60]
    for r in results:
        mark = "PASS" if r.passed else "FAIL"
        lines.append(f"[{mark}] #{r.id} {r.category}: {r.question}")
        lines.append(f"        {r.detail}")
    passed = sum(1 for r in results if r.passed)
    lines.append("-" * 60)
    lines.append(f"{passed}/{len(results)} cases passed")
    return "\n".join(lines)
