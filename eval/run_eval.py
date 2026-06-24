"""
Eval harness for the ML/MLOps Study Buddy.
Judge: llama3.2:3b via Ollama (same model, local, no key needed).

Run with:
    python eval/run_eval.py
"""

from __future__ import annotations
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_service import ChatService

HERE = os.path.dirname(os.path.abspath(__file__))

JUDGE_PROMPT = """You are a strict but fair evaluator.

Question: {question}
Expected answer (key points): {expected}
Actual answer: {actual}

Does the actual answer address the key points in the expected answer?
Reply with exactly one word: PASS or FAIL."""


def load_cases() -> list[dict]:
    with open(os.path.join(HERE, "eval_cases.json")) as f:
        return json.load(f)["cases"]


def judge(case: dict, answer: str) -> bool:
    """Use llama3.2:3b as the judge — returns True for PASS."""
    judge_service = ChatService(temperature=0.0)
    prompt = JUDGE_PROMPT.format(
        question=case["input"],
        expected=case["expected"],
        actual=answer,
    )
    verdict = judge_service.send(prompt).strip().upper()
    # Accept PASS even if model adds punctuation e.g. "PASS."
    return verdict.startswith("PASS")


def run_variant(label: str, temperature: float) -> tuple[int, int]:
    cases = load_cases()
    service = ChatService(temperature=temperature)
    passed = 0

    print(f"\n{'='*50}")
    print(f"Variant: {label}  (temperature={temperature})")
    print(f"{'='*50}")

    for case in cases:
        service.reset()
        answer = service.send(case["input"])
        ok = judge(case, answer)
        passed += int(ok)
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] case {case['id']:>2} | {case['input'][:55]}...")

    total = len(cases)
    rate = (passed / total * 100) if total else 0
    print(f"\nResult: {passed}/{total} passed ({rate:.0f}%)")
    return passed, total


if __name__ == "__main__":
    results = []

    p, t = run_variant("Variant-A  strict  (temp=0.2)", temperature=0.2)
    results.append(("Variant-A (temp=0.2)", p, t))

    p, t = run_variant("Variant-B  creative (temp=0.8)", temperature=0.8)
    results.append(("Variant-B (temp=0.8)", p, t))

    print("\n" + "="*50)
    print("PASS-RATE TABLE")
    print("="*50)
    print(f"{'Variant':<30} {'Cases':>6} {'Passed':>7} {'Pass rate':>10}")
    print("-"*55)
    for label, passed, total in results:
        rate = (passed / total * 100) if total else 0
        print(f"{label:<30} {total:>6} {passed:>7} {rate:>9.0f}%")