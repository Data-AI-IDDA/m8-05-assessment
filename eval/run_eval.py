"""
Run the eval over eval_cases.json and print a pass-rate table.

    python eval/run_eval.py

Each case's input is sent through a ChatService, then scored. Grading is
hybrid:
  - cases with 'must_include' / 'must_exclude' get a deterministic keyword
    check (reliable for facts and safety behaviour);
  - the rest get an LLM-as-judge call (the same local model) against the
    case's rubric.
We run two variants — a focused temperature and a hotter one — to see whether
sampling moves the pass rate. The test set is fixed so the runs are comparable.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_service import ChatService  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

JUDGE_PROMPT = """You grade answers from a Python tutoring assistant. Be \
lenient: an answer PASSES if it conveys the key idea in the rubric, even if it \
adds extra correct detail or phrases things differently. It only FAILS if it is \
wrong, off-topic, or misses the key idea.

Question asked:
{question}

What a passing answer must convey (rubric):
{rubric}

The assistant actually answered:
{answer}

Reply with exactly one word on its own: PASS or FAIL."""


def load_cases() -> list[dict]:
    with open(os.path.join(HERE, "eval_cases.json")) as f:
        return json.load(f)["cases"]


def keyword_check(case: dict, answer: str) -> bool:
    """Deterministic grading: all required substrings present, none forbidden."""
    low = answer.lower()
    for token in case.get("must_include", []):
        if token.lower() not in low:
            return False
    for token in case.get("must_exclude", []):
        if token.lower() in low:
            return False
    return True


def judge(case: dict, answer: str, judge_service: ChatService) -> bool:
    """Score one answer: keyword check if defined, else LLM-as-judge."""
    if "must_include" in case or "must_exclude" in case:
        return keyword_check(case, answer)
    judge_service.reset()
    verdict = judge_service.send(
        JUDGE_PROMPT.format(
            question=case["input"],
            rubric=case["expected"],
            answer=answer,
        )
    )
    return "PASS" in verdict.upper()


def run_variant(label: str, temperature: float, judge_service: ChatService) -> tuple[int, int]:
    cases = load_cases()
    service = ChatService(temperature=temperature)
    passed = 0
    print(f"\n=== {label} (temperature={temperature}) ===")
    for case in cases:
        service.reset()
        answer = service.send(case["input"])
        ok = judge(case, answer, judge_service)
        passed += int(ok)
        print(f"  [{'PASS' if ok else 'FAIL'}] case {case['id']}: {case['input'][:55]!r}")
    total = len(cases)
    rate = (passed / total * 100) if total else 0
    print(f"{label}: {passed}/{total} passed ({rate:.0f}%)")
    return passed, total


if __name__ == "__main__":
    # The judge uses temperature 0 so its grading is as stable as possible.
    judge_service = ChatService(temperature=0.0)

    results = []
    for label, temp in [("variant-A focused", 0.2), ("variant-B hot", 0.9)]:
        passed, total = run_variant(label, temp, judge_service)
        results.append((label, temp, passed, total))

    print("\n\n## Pass-rate table\n")
    print("| Variant | Temp | Cases | Passed | Pass rate |")
    print("|---------|------|-------|--------|-----------|")
    for label, temp, passed, total in results:
        rate = (passed / total * 100) if total else 0
        print(f"| {label} | {temp} | {total} | {passed} | {rate:.0f}% |")
