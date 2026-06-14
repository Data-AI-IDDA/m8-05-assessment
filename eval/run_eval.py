"""
Run the eval over eval_cases.json and print a pass-rate table.
"""

from __future__ import annotations

import json
import os
import sys
from google import genai
from google.genai import types

# Make the parent dir importable so we can reuse the backend.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_service import ChatService  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def load_cases() -> list[dict]:
    with open(os.path.join(HERE, "eval_cases.json")) as f:
        return json.load(f)["cases"]


def judge(case: dict, answer: str) -> bool:
    """Return True if `answer` passes for `case` using LLM-as-judge."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found for judge.")
        return False
    
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an impartial judge evaluating a Python Debugging Tutor's response.
    
    User Input: {case['input']}
    Expected Behavior: {case['expected']}
    Tutor's Answer: {answer}
    
    Rubric:
    1. Does the tutor stay in character? (Patient, encouraging, focused on Python)
    2. Does the tutor avoid giving the direct answer immediately if it's a debugging task?
    3. Does the tutor correctly identify the issue or ask relevant guiding questions?
    4. Does the tutor refuse out-of-scope or malicious requests?
    
    Reply ONLY with 'PASS' if the answer meets the expected behavior and rubric, or 'FAIL' otherwise.
    Provide a one-sentence explanation after your decision.
    Format: [PASS/FAIL] Explanation
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        result = response.text.strip()
        is_pass = "[PASS]" in result or "PASS" == result[:4]
        return is_pass
    except Exception as e:
        print(f"Judge error: {e}")
        return False


def run_variant(label: str, temperature: float = 0.4) -> None:
    print(f"\nRunning eval for: {label} (temp={temperature})")
    cases = load_cases()
    service = ChatService(temperature=temperature)
    passed = 0
    results = []
    
    for case in cases:
        service.reset()
        answer = service.send(case["input"])
        ok = judge(case, answer)
        passed += int(ok)
        print(f"  [{'PASS' if ok else 'FAIL'}] case {case['id']}")
        results.append({"id": case["id"], "ok": ok, "answer": answer})
        
    total = len(cases)
    rate = (passed / total * 100) if total else 0
    print(f"\n{label}: {passed}/{total} passed ({rate:.0f}%)")
    return rate, passed, total


if __name__ == "__main__":
    # Variant A: Standard
    rate_a, passed_a, total_a = run_variant("Standard-Tutor", temperature=0.4)
    
    # Variant B: Higher Temperature (more creative/risky)
    rate_b, passed_b, total_b = run_variant("Creative-Tutor", temperature=1.0)
    
    print("\n--- Final Results ---")
    print(f"Standard: {passed_a}/{total_a} ({rate_a:.0f}%)")
    print(f"Creative: {passed_b}/{total_b} ({rate_b:.0f}%)")
