"""
Run the eval over eval_cases.json and print a pass-rate table.

Usage:
    python eval/run_eval.py

Approach: send each case's input through ChatService, then score the output
with an LLM-as-judge call (same Ollama model, separate one-off call with its
own judge system prompt — NOT the MealPlanner ChatService, so the judge
isn't subject to the assistant's scope restrictions).

Runs TWO variants (different temperature settings) so we can compare.
"""

from __future__ import annotations

import json
import os
import sys

import requests

# Make the parent dir importable so we can reuse the backend.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_service import ChatService, OLLAMA_HOST  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

JUDGE_MODEL = os.environ.get("MODEL", "llama3.2")

JUDGE_SYSTEM_PROMPT = """You are an evaluation judge. You will be given a
USER QUESTION, an EXPECTED criteria description, and the ASSISTANT'S ANSWER.

Decide if the ASSISTANT'S ANSWER satisfies the EXPECTED criteria.
Reply with exactly one word: PASS or FAIL. No explanation."""


def load_cases() -> list[dict]:
    with open(os.path.join(HERE, "eval_cases.json")) as f:
        return json.load(f)["cases"]


def call_judge(prompt: str) -> str:
    """One-off call to Ollama with the judge system prompt (bypasses
    ChatService / MealPlanner system prompt entirely)."""
    resp = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": JUDGE_MODEL,
            "messages": [
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "options": {"temperature": 0.0},
            "stream": False,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json().get("message", {}).get("content", "")


def judge(case: dict, answer: str) -> bool:
    """Return True if `answer` passes for `case` (LLM-as-judge)."""
    prompt = (
        f"USER QUESTION:\n{case['input']}\n\n"
        f"EXPECTED:\n{case['expected']}\n\n"
        f"ASSISTANT'S ANSWER:\n{answer}\n\n"
        f"PASS or FAIL?"
    )
    verdict = call_judge(prompt).strip().upper()
    return verdict.startswith("PASS")


def run_variant(label: str, model: str, temperature: float) -> tuple[int, int]:
    cases = load_cases()
    service = ChatService(model=model, temperature=temperature)
    passed = 0
    print(f"\n=== {label} (model={model}, temperature={temperature}) ===")
    for case in cases:
        service.reset()
        answer = service.send(case["input"])
        ok = judge(case, answer)
        passed += int(ok)
        print(f"  [{'PASS' if ok else 'FAIL'}] case {case['id']}: {case['input'][:60]!r}")
    total = len(cases)
    rate = (passed / total * 100) if total else 0
    print(f"\n{label}: {passed}/{total} passed ({rate:.0f}%)")
    return passed, total


if __name__ == "__main__":
    model = os.environ.get("MODEL", "llama3.2")

    results = []
    results.append(("variant-A (temperature=0.7)", *run_variant("variant-A", model, 0.7)))
    results.append(("variant-B (temperature=0.0)", *run_variant("variant-B", model, 0.0)))

    print("\n\n| Variant | Cases | Passed | Pass rate |")
    print("|---------|-------|--------|-----------|")
    for label, passed, total in results:
        rate = (passed / total * 100) if total else 0
        print(f"| {label} | {total} | {passed} | {rate:.0f}% |")