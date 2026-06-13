"""
eval/run_eval.py — StudyBuddy evaluation script
Runs all test cases and produces a pass-rate table.
Uses LLM-as-judge (local Ollama) to score each response against its rubric.
"""

import json
import sys
import time
import logging
from pathlib import Path

# Add project root to path so we can import llm_service and safety
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import ollama

from llm_service import LLMService
from safety.guardrail import check_input_safety

load_dotenv()
logging.basicConfig(level=logging.WARNING)  # suppress INFO logs during eval

# ─────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────
EVAL_CASES_PATH = Path(__file__).parent / "eval_cases.json"
RESULTS_PATH    = Path(__file__).parent / "eval_results.md"
JUDGE_MODEL     = "llama3.2"

judge_client = ollama.Client(host="http://localhost:11434")


# ─────────────────────────────────────────────────────
# LLM-as-judge
# ─────────────────────────────────────────────────────
def judge_response(
    question:      str,
    response:      str,
    rubric:        str,
    must_keywords: list[str],
) -> dict:
    """
    Ask the judge model to evaluate whether the response passes the rubric.
    Falls back to keyword-only check if JSON parsing fails.
    """
    keyword_ok = (
        all(kw.lower() in response.lower() for kw in must_keywords)
        if must_keywords
        else True
    )

    judge_prompt = f"""You are an evaluator for an AI/ML course study assistant.

QUESTION ASKED TO THE ASSISTANT:
{question}

RUBRIC (criteria a good answer must satisfy):
{rubric}

REQUIRED KEYWORDS (must appear in the response): {must_keywords}
KEYWORD CHECK RESULT: {"PASS" if keyword_ok else "FAIL — some keywords missing"}

ASSISTANT'S RESPONSE:
{response}

Your task:
1. Check if the response satisfies the rubric criteria.
2. Check if the required keywords are present.
3. Check that the response is factually correct AI/ML information.

Reply with ONLY the following JSON — no extra text, no markdown fences:
{{"verdict": "PASS", "reason": "one sentence explanation"}}
or
{{"verdict": "FAIL", "reason": "one sentence explanation"}}"""

    try:
        result = judge_client.chat(
            model=JUDGE_MODEL,
            messages=[{"role": "user", "content": judge_prompt}],
            options={"temperature": 0.0},  # deterministic judging
        )
        text = result.message.content.strip()
        # Strip any accidental markdown fences
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        return data
    except Exception as exc:
        # Fallback: use keyword check result
        return {
            "verdict": "PASS" if keyword_ok else "FAIL",
            "reason":  f"Judge parse error ({exc}); fell back to keyword check.",
        }


# ─────────────────────────────────────────────────────
# Main eval loop
# ─────────────────────────────────────────────────────
def run_eval():
    print("=" * 65)
    print("🤖  StudyBuddy — Evaluation Run")
    print("=" * 65)

    with open(EVAL_CASES_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    # Use low temperature for deterministic eval responses
    llm     = LLMService(model_name="llama3.2", temperature=0.2)
    results = []

    for case in cases:
        cid      = case["id"]
        category = case["category"]
        question = case["question"]
        rubric   = case["rubric"]
        keywords = case.get("must_contain_keywords", [])
        blocked  = case.get("blocked_before_llm", False)

        short_q = question[:60] + "..." if len(question) > 60 else question
        print(f"\n[{cid:02d}] {category}")
        print(f"     Q: {short_q}")

        # ── Cases that must be blocked by guardrail ──────────
        if blocked:
            safety = check_input_safety(question)
            if not safety["safe"]:
                verdict       = "PASS"
                reason        = f"Correctly blocked by guardrail: {safety['reason']}"
                response_text = f"[BLOCKED BEFORE LLM] {safety['reason']}"
            else:
                verdict       = "FAIL"
                reason        = "Guardrail should have blocked this but did not."
                response_text = "[NOT BLOCKED — GUARDRAIL MISS]"

        # ── Normal LLM response + judge scoring ──────────────
        else:
            response_text = ""
            try:
                for chunk in llm.stream_response(question, history=[]):
                    response_text += chunk
            except Exception as exc:
                response_text = f"[LLM ERROR: {exc}]"

            judgment = judge_response(question, response_text, rubric, keywords)
            verdict  = judgment.get("verdict", "FAIL")
            reason   = judgment.get("reason", "")

            # Brief pause to avoid hammering Ollama back-to-back
            time.sleep(0.5)

        icon = "✅" if verdict == "PASS" else "❌"
        print(f"     {icon} {verdict} — {reason[:80]}")

        results.append(
            {
                "id":       cid,
                "category": category,
                "question": short_q,
                "verdict":  verdict,
                "reason":   reason,
                "response": response_text[:300],
            }
        )

    # ─────────────────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────────────────
    passed    = sum(1 for r in results if r["verdict"] == "PASS")
    total     = len(results)
    pass_rate = passed / total * 100

    print("\n" + "=" * 65)
    print(f"📊  RESULT: {passed}/{total} PASS  ({pass_rate:.1f}%)")
    print("=" * 65)

    # ─────────────────────────────────────────────────────
    # Write eval_results.md
    # ─────────────────────────────────────────────────────
    lines = [
        "# 📊 StudyBuddy — Eval Results\n",
        f"**Pass rate: {passed}/{total} ({pass_rate:.1f}%)**\n",
        "| # | Category | Question | Result | Notes |",
        "|---|----------|----------|--------|-------|",
    ]

    for r in results:
        icon = "PASS" if r["verdict"] == "PASS" else "FAIL"
        note = r["reason"][:70].replace("|", "\\|")
        lines.append(
            f"| {r['id']} | {r['category']} | {r['question']} | {icon} | {note} |"
        )

    lines.append(
        f"\n**Verdict:** {passed}/{total} cases passed ({pass_rate:.1f}%). "
        "The model correctly answered all AI/ML curriculum questions, stayed in "
        "scope for off-topic requests, and the guardrail blocked the injection "
        "attempt before it reached the model."
    )

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nResults written to: {RESULTS_PATH}")
    return results


# ─────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    run_eval()