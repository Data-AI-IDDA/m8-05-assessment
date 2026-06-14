"""
Eval harness for ChefBot.

Runs each case in eval_cases.json through the ChatService, then uses
Gemini-as-judge to score the response against the rubric.

Usage:
    python eval/run_eval.py

Output:
    Pass-rate table printed to stdout and written to eval/eval_results.md
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
import time
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

# Allow imports from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))
from llm_service import ChatService

load_dotenv()

CASES_FILE = Path(__file__).parent / "eval_cases.json"
RESULTS_FILE = Path(__file__).parent / "eval_results.md"

JUDGE_PROMPT = """You are an impartial evaluator for a recipe and meal-planning chatbot.

Rubric: {rubric}

Bot response:
\"\"\"
{response}
\"\"\"

Does the bot response satisfy the rubric? Reply with exactly one word: PASS or FAIL.
Then on the next line give a one-sentence reason.
"""


def judge(rubric: str, response: str, judge_model: genai.GenerativeModel) -> tuple[str, str]:
    prompt = JUDGE_PROMPT.format(rubric=rubric, response=response)
    result = judge_model.generate_content(prompt)
    lines = result.text.strip().splitlines()
    verdict = lines[0].strip().upper() if lines else "FAIL"
    verdict = "PASS" if "PASS" in verdict else "FAIL"
    reason = lines[1].strip() if len(lines) > 1 else "No reason given."
    return verdict, reason


def run_eval() -> None:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: Set GEMINI_API_KEY in .env")
        sys.exit(1)

    genai.configure(api_key=api_key)
    judge_model = genai.GenerativeModel(
        "gemini-2.0-flash",
        generation_config=genai.GenerationConfig(temperature=0.0, max_output_tokens=256),
    )

    cases = json.loads(CASES_FILE.read_text())

    rows = []
    passed = 0

    for case in cases:
        cid = case["id"]
        desc = case["description"]
        user_input = case["user_input"]
        rubric = case["rubric"]
        prior = case.get("prior_context", [])

        print(f"Running {cid}: {desc} ...", end=" ", flush=True)

        # Build service fresh for each case
        service = ChatService(temperature=0.0)

        # Inject prior context if any
        service.history = prior

        # Get bot response (non-streaming for eval)
        try:
            response = service.send(user_input)
        except Exception as e:
            response = f"ERROR: {e}"

        # Judge
        time.sleep(0.5)  # gentle rate-limit
        try:
            verdict, reason = judge(rubric, response, judge_model)
        except Exception as e:
            verdict, reason = "FAIL", f"Judge error: {e}"

        if verdict == "PASS":
            passed += 1

        rows.append({
            "id": cid,
            "description": desc,
            "verdict": verdict,
            "reason": reason,
            "response_snippet": textwrap.shorten(response, width=120),
        })
        print(verdict)

    total = len(cases)
    pass_rate = passed / total * 100

    # ── Print table ──────────────────────────────────────────────────────────

    header = f"{'ID':<5} {'Description':<40} {'Verdict':<8} Reason"
    sep = "-" * len(header)
    print()
    print(sep)
    print(header)
    print(sep)
    for r in rows:
        verdict_str = "✅ PASS" if r["verdict"] == "PASS" else "❌ FAIL"
        print(f"{r['id']:<5} {r['description']:<40} {verdict_str:<8} {r['reason']}")
    print(sep)
    print(f"\nPass rate: {passed}/{total} = {pass_rate:.0f}%\n")

    # ── Write markdown results ────────────────────────────────────────────────

    md_lines = [
        "# ChefBot Eval Results",
        "",
        f"**Pass rate: {passed}/{total} = {pass_rate:.0f}%**",
        "",
        "| ID | Description | Verdict | Reason |",
        "|----|-------------|---------|--------|",
    ]
    for r in rows:
        emoji = "✅" if r["verdict"] == "PASS" else "❌"
        md_lines.append(
            f"| {r['id']} | {r['description']} | {emoji} {r['verdict']} | {r['reason']} |"
        )
    md_lines += [
        "",
        "## Verdict",
        "",
        f"ChefBot passed {passed} out of {total} eval cases ({pass_rate:.0f}%).",
        "The eval covers basic recipe knowledge, dietary adaptations, out-of-scope refusals,",
        "prompt-injection resistance, and multi-turn context retention.",
        "A pass rate ≥ 80% indicates the assistant is reliable for its intended use case.",
    ]

    RESULTS_FILE.write_text("\n".join(md_lines))
    print(f"Results written to {RESULTS_FILE}")


if __name__ == "__main__":
    run_eval()
