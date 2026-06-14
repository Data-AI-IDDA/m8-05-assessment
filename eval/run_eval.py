"""
Eval harness for CodeLens — AI Code Explainer.

Uses LLM-as-judge (gemini-2.5-flash) to score each answer PASS/FAIL.
Runs two variants:
  - variant-A: temperature=0.2  (more deterministic)
  - variant-B: temperature=0.7  (more creative)

API-limit friendly design:
  - Each case gets ONE ChatService.send() call (the answer)
  - Each answer gets ONE judge call  → 2 calls per case per variant
  - Total API calls: 2 variants × 5 cases × 2 = 20 calls maximum
  - 13-second delay between variants (RPM=5 → 1 req per 12s to be safe)
  - 13-second delay between each call within a variant
  - judge uses max_output_tokens=64 (tiny, fast, cheap)

Run:
    python eval/run_eval.py
    python eval/run_eval.py --variant A   # run only variant A (10 calls)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

from llm_service import ChatService  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# ── Judge config ───────────────────────────────────────────────────────────────
JUDGE_MODEL = "gemini-2.5-flash"

# RPM=5 means max 1 request every 12 seconds to be safe
DELAY_BETWEEN_CALLS = 13  # seconds between every API call (answer + judge)
DELAY_BETWEEN_VARIANTS = 60  # seconds pause between variant A and B

JUDGE_PROMPT_TEMPLATE = """\
You are a strict but fair evaluator for an AI code-explanation assistant called CodeLens.

## Task
Decide whether the ACTUAL ANSWER satisfies the EXPECTED CRITERIA for the given INPUT.

## Input
{input}

## Expected criteria
{expected}

## Actual answer
{answer}

## Scoring rules
- Reply with exactly one word: PASS or FAIL
- PASS  -> the answer clearly satisfies the criteria (even if worded differently)
- FAIL  -> the answer ignores or violates the criteria
- Do not add any explanation — just PASS or FAIL.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_cases() -> list[dict]:
    path = os.path.join(HERE, "eval_cases.json")
    with open(path) as f:
        return json.load(f)["cases"]


def get_judge_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set — check your .env file.")
    return genai.Client(api_key=api_key)


def judge(client: genai.Client, case: dict, answer: str) -> tuple[bool, str]:
    """Call the judge model. Returns (passed: bool, verdict: str)."""
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        input=case["input"],
        expected=case["expected"],
        answer=answer,
    )
    response = client.models.generate_content(
        model=JUDGE_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,       # deterministic judge
            max_output_tokens=64,  # only needs PASS or FAIL
        ),
    )
    verdict = (response.text or "FAIL").strip().upper()
    # model sometimes returns "PASS." or "PASS\n" — clean it
    verdict = verdict.split()[0] if verdict else "FAIL"
    passed = verdict == "PASS"
    return passed, verdict


# ── Variant runner ─────────────────────────────────────────────────────────────

def run_variant(
    label: str,
    temperature: float,
    cases: list[dict],
    judge_client: genai.Client,
    verbose: bool = True,
) -> dict:
    """
    Run all cases through ChatService at the given temperature.
    Returns a summary dict.
    """
    results = []
    passed_count = 0

    if verbose:
        print(f"\n{'='*55}")
        print(f"  Variant: {label}  (temperature={temperature})")
        print(f"{'='*55}")

    for i, case in enumerate(cases):
        # Fresh service per case — no history bleed between cases
        service = ChatService(temperature=temperature)

        # ── Get model answer ──────────────────────────────────────
        try:
            answer = service.send(case["input"])
        except Exception as exc:
            answer = f"[ERROR getting answer: {exc}]"

        if verbose:
            print(f"  Waiting {DELAY_BETWEEN_CALLS}s before judge call…")
        time.sleep(DELAY_BETWEEN_CALLS)

        # ── Judge the answer ──────────────────────────────────────
        try:
            passed, verdict = judge(judge_client, case, answer)
        except Exception as exc:
            passed, verdict = False, f"JUDGE_ERROR: {exc}"

        passed_count += int(passed)
        results.append({
            "id": case["id"],
            "category": case.get("category", ""),
            "passed": passed,
            "verdict": verdict,
            "answer_preview": answer[:120].replace("\n", " "),
        })

        if verbose:
            status = "PASS" if passed else "FAIL"
            print(f"  [{status}] case {case['id']:>2} ({case.get('category', '')})")
            if not passed:
                print(f"         preview: {answer[:100].replace(chr(10), ' ')}…")

        # Delay before next case (skip after last case)
        if i < len(cases) - 1:
            if verbose:
                print(f"  Waiting {DELAY_BETWEEN_CALLS}s before next case…")
            time.sleep(DELAY_BETWEEN_CALLS)

    total = len(cases)
    rate = (passed_count / total * 100) if total else 0.0

    if verbose:
        print(f"\n  -> {passed_count}/{total} passed ({rate:.0f}%)\n")

    return {
        "label": label,
        "temperature": temperature,
        "passed": passed_count,
        "total": total,
        "pass_rate": rate,
        "results": results,
    }


# ── Table printer ──────────────────────────────────────────────────────────────

def print_summary_table(summaries: list[dict]) -> None:
    print("\n" + "="*55)
    print("  PASS-RATE SUMMARY")
    print("="*55)
    print(f"  {'Variant':<25} {'Temp':>5}  {'Passed':>8}  {'Rate':>7}")
    print("  " + "-"*50)
    for s in summaries:
        print(
            f"  {s['label']:<25} {s['temperature']:>5.1f}"
            f"  {s['passed']:>2}/{s['total']:<5}  {s['pass_rate']:>5.0f}%"
        )
    print("="*55)


def print_markdown_table(summaries: list[dict]) -> None:
    """Print a Markdown table suitable for pasting into eval_results.md."""
    print("\n### Markdown table (paste into eval_results.md)\n")
    print("| Variant | Temp | Cases | Passed | Pass rate |")
    print("|---------|------|-------|--------|-----------|")
    for s in summaries:
        print(
            f"| {s['label']} | {s['temperature']} "
            f"| {s['total']} | {s['passed']} | {s['pass_rate']:.0f}% |"
        )

    print("\n#### Per-case breakdown\n")
    if summaries:
        first = summaries[0]
        header = "| Case | Category | " + " | ".join(s["label"] for s in summaries) + " |"
        sep = "|------|----------" + "|--------" * len(summaries) + "|"
        print(header)
        print(sep)
        for i, r in enumerate(first["results"]):
            row = f"| {r['id']} | {r['category']} |"
            for s in summaries:
                v = "PASS" if s["results"][i]["passed"] else "FAIL"
                row += f" {v} |"
            print(row)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Run CodeLens eval")
    parser.add_argument(
        "--variant",
        choices=["A", "B", "both"],
        default="both",
        help="Which variant(s) to run (default: both)",
    )
    args = parser.parse_args()

    cases = load_cases()
    judge_client = get_judge_client()

    summaries = []

    VARIANTS = {
        "A": ("variant-A (temp=0.2)", 0.2),
        "B": ("variant-B (temp=0.7)", 0.7),
    }

    to_run = ["A", "B"] if args.variant == "both" else [args.variant]

    for vi, key in enumerate(to_run):
        label, temp = VARIANTS[key]
        summary = run_variant(label, temp, cases, judge_client, verbose=True)
        summaries.append(summary)

        # Pause between variants to reset the RPM window
        if vi < len(to_run) - 1:
            print(f"\n  Pausing {DELAY_BETWEEN_VARIANTS}s between variants to reset RPM window…\n")
            time.sleep(DELAY_BETWEEN_VARIANTS)

    print_summary_table(summaries)
    print_markdown_table(summaries)

    print("\nDone. Copy the Markdown table above into eval/eval_results.md.\n")


if __name__ == "__main__":
    main()
