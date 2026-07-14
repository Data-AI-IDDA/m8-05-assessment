import json
import os
import sys
from google import genai

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_service import ChatService

HERE = os.path.dirname(os.path.abspath(__file__))

def load_cases() -> list[dict]:
    with open(os.path.join(HERE, "eval_cases.json")) as f:
        return json.load(f)["cases"]

def judge(case: dict, answer: str, judge_client: genai.Client) -> bool:
    """LLM-as-judge using a strict rubric prompt."""
    prompt = f"""You are an impartial evaluator grading an LLM's response.
    
    [Input Query]
    {case['input']}
    
    [Expected Criteria]
    {case['expected']}
    
    [Actual Answer]
    {answer}
    
    Evaluate if the Actual Answer strictly meets the Expected Criteria. 
    Respond with exactly one word: PASS or FAIL.
    """
    
    response = judge_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    result = response.text.strip().upper()
    return "PASS" in result

def run_variant(label: str, temperature: float) -> None:
    cases = load_cases()
    service = ChatService(temperature=temperature)
    judge_client = genai.Client() # Independent client for the judge
    
    passed = 0
    print(f"\nRunning Eval for: {label} (Temp: {temperature})")
    print("-" * 40)
    
    for case in cases:
        service.reset()
        
        # We must collect the stream into a single string for the judge
        answer_generator = service.stream(case["input"])
        answer = "".join([chunk for chunk in answer_generator])
        
        ok = judge(case, answer, judge_client)
        passed += int(ok)
        print(f"  [{'PASS' if ok else 'FAIL'}] Case {case['id']}: {case['input'][:40]}...")
        
    total = len(cases)
    rate = (passed / total * 100) if total else 0
    print(f"\nResult {label}: {passed}/{total} passed ({rate:.0f}%)")

if __name__ == "__main__":
    run_variant("Variant A (Low Temp)", temperature=0.2)
    run_variant("Variant B (High Temp)", temperature=0.8)