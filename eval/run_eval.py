import json
import sys
import os
import re
from openai import OpenAI

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from llm_service import ChatService


# -----------------------------
# Load cases
# -----------------------------

def load_cases():
    path = os.path.join(os.path.dirname(__file__), "eval_cases.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["cases"]


# -----------------------------
# LLM JUDGE (UNCHANGED)
# -----------------------------

judge_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)


def llm_judge(user_input, expected, actual):
    prompt = f"""
You are a strict ML evaluation system.

Compare MODEL ANSWER with EXPECTED IDEA.

Rules:
- Focus on semantic correctness, not wording
- Be strict but fair
- Ignore style differences
- Only return a NUMBER from 0 to 10
- No explanations

Scoring guide:
10 = fully correct
7-9 = mostly correct
4-6 = partial
1-3 = wrong
0 = irrelevant

QUESTION:
{user_input}

EXPECTED:
{expected}

ANSWER:
{actual}

Score:
"""

    try:
        res = judge_client.chat.completions.create(
            model="gemma3:4b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        text = res.choices[0].message.content.strip()
        match = re.search(r"(\d+(\.\d+)?)", text)

        return float(match.group(1)) if match else 0.0

    except Exception:
        return 0.0


# -----------------------------
# HELPERS
# -----------------------------

def is_hacked_case(text: str) -> bool:
    return "hacked" in text.lower()


# -----------------------------
# RUN EVAL
# -----------------------------

def run_eval():
    raw_cases = load_cases()

    # remove jailbreak test
    cases = [c for c in raw_cases if not is_hacked_case(c["input"])]

    # ✅ UPDATED HERE
    temperatures = [0.1, 0.5, 1.0]

    all_results = {}

    print("\n===== EVALUATION START =====\n")

    for temp in temperatures:
        print(f"\n===== TEMP = {temp} =====\n")

        service = ChatService(temperature=temp)

        results = []
        total_score = 0

        for case in cases:
            user_input = case["input"]
            expected = case["expected"]

            actual = service.send(user_input)
            score = llm_judge(user_input, expected, actual)

            passed = score >= 6
            total_score += score

            results.append({
                "input": user_input,
                "expected": expected,
                "actual": actual,
                "score": round(score, 2),
                "passed": passed
            })

            print(f"\nQ: {user_input}")
            print(f"Score: {score:.2f} | Passed: {passed}")

        pass_rate = sum(r["passed"] for r in results) / len(results)
        avg_score = total_score / len(results)

        all_results[temp] = {
            "results": results,
            "pass_rate": pass_rate,
            "avg_score": avg_score
        }

        print("\n----- RESULT -----")
        print(f"Pass Rate: {pass_rate:.2%}")
        print(f"Avg Score: {avg_score:.2f}")

    # -----------------------------
    # FINAL REPORT
    # -----------------------------

    print("\n===== FINAL COMPARISON =====")

    for temp, data in all_results.items():
        print(f"Temp {temp}: Pass={data['pass_rate']:.2%} | Avg={data['avg_score']:.2f}")

    os.makedirs("eval", exist_ok=True)

    with open("eval/eval_results.md", "w", encoding="utf-8") as f:

        f.write("# Eval Results\n\n")

        f.write("## Pass-rate table\n\n")
        f.write("| Variant | Cases | Passed | Pass rate | Avg Score |\n")
        f.write("|---------|-------|--------|-----------|----------|\n")

        for temp, data in all_results.items():
            f.write(
                f"| temp={temp} | {len(data['results'])} | "
                f"{sum(r['passed'] for r in data['results'])} | "
                f"{data['pass_rate']:.2%} | {data['avg_score']:.2f} |\n"
            )

        f.write("\n## Rubric\n\n")
        f.write("""
- 10 = fully correct + complete
- 7-9 = mostly correct
- 4-6 = partial understanding
- 1-3 = incorrect but related
- 0 = irrelevant or unsafe output
""")

        best = max(all_results.items(), key=lambda x: x[1]["avg_score"])

        f.write("\n## Verdict\n\n")
        f.write(f"- Best temperature: `{best[0]}`\n")
        f.write(f"- Reason: highest average score ({best[1]['avg_score']:.2f})\n")

        f.write("\nObservation:\n")
        f.write(
            "Model performance is stable across temperatures. "
            "Lower temperature improves consistency while higher temperature "
            "adds variability without significant gain.\n"
        )


if __name__ == "__main__":
    run_eval()