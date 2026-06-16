"""
Run the eval over eval_cases.json and print a pass-rate table.

STARTER skeleton. Fill in the TODOs, then:

    python eval/run_eval.py

Approach: send each case's input through your ChatService, then score the
output. LLM-as-judge is fine — give a judge model a clear rubric and ask for
a pass/fail (or 1–5). Keep the test set FIXED so you can compare changes.
"""

from __future__ import annotations

import json
import os
import sys

# Make the parent dir importable so we can reuse the backend.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_service import ChatService  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def load_cases() -> list[dict]:
    with open(os.path.join(HERE, "eval_cases.json")) as f:
        return json.load(f)["cases"]


def judge(case: dict, answer: str) -> bool:
    """Return True if `answer` contains any of our target validation keywords."""
    expected_keywords = case.get("expected_keywords", [])
    return any(keyword.lower() in answer.lower() for keyword in expected_keywords)


def run_variant(label: str, temperature: float) -> dict[str, float]:
    cases = load_cases()
    service = ChatService(temperature=temperature)
    
    category_stats = {}
    passed = 0
    
    print(f"\n🚀 Running Evaluation Framework: {label} (Temp: {temperature})...")
    
    for case in cases:
        service.reset()
        category = case["category"]
        
        # Get response from microservice
        answer = service.send(case["input"])
        ok = judge(case, answer)
        passed += int(ok)
        
        # Initialize category counters
        if category not in category_stats:
            category_stats[category] = {"passed": 0, "total": 0}
        category_stats[category]["total"] += 1
        if ok:
            category_stats[category]["passed"] += 1
            
        print(f"  [{'PASS' if ok else 'FAIL'}] Case #{case['id']} ({category})")
        
    total = len(cases)
    overall_rate = (passed / total * 100) if total else 0
    print(f"✨ {label} Summary: {passed}/{total} passed ({overall_rate:.1f}%)")
    
    # Flatten stats to return for comparison table construction
    report = {cat: (stats["passed"] / stats["total"] * 100) for cat, stats in category_stats.items()}
    report["OVERALL"] = overall_rate
    return report


if __name__ == "__main__":
    # Run two variants to evaluate performance differences across sampling parameters
    results_a = run_variant("Variant-A (Strict Learning)", temperature=0.0)
    results_b = run_variant("Variant-B (High Creativity)", temperature=1.2)
    
    # Format and display the final Markdown evaluation comparison table
    print("\n### Evaluation Pass-Rate Comparison Table\n")
    print("| Evaluation Category | Variant-A Pass Rate (Deterministic) | Variant-B Pass Rate (Creative) |")
    print("| --- | --- | --- |")
    for cat in ["Computer Vision", "LLMs", "Out of Scope", "Safety", "OVERALL"]:
        rate_a = results_a.get(cat, 0.0)
        rate_b = results_b.get(cat, 0.0)
        if cat == "OVERALL":
            print(f"| **{cat}** | **{rate_a:.1f}%** | **{rate_b:.1f}%** |")
        else:
            print(f"| {cat} | {rate_a:.1f}% | {rate_b:.1f}% |")