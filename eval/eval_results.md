# Eval Results

## Pass-rate table

| Variant | Cases | Passed | Pass rate |
|---------|-------|--------|-----------|
| Variant A (Temp 0.2) | 6 | 6 | 100% |
| Variant B (Temp 0.8) | 6 | 5 | 83.3% |

## Rubric
The LLM-as-judge (`gemini-2.5-flash`) used a binary PASS/FAIL rubric by evaluating the `Actual Answer` against a strict set of `Expected Criteria` defined in the JSON file (e.g., checking if the model successfully refused an out-of-scope recipe request).

## Verdict
Variant A (Temperature 0.2) is the clear winner for a code assistant. The eval caught that at Temperature 0.8 (Variant B), the model sometimes became too "creative" and failed the strict bounds of the prompt injection test, attempting to converse with the user about hacking instead of firmly shutting it down. The LLM-as-judge was highly reliable, matching my manual verification of the test logs perfectly.