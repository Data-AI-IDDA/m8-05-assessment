# Eval Results

## Pass-rate table

| Variant | Cases | Passed | Pass rate | Avg Score |
|---------|-------|--------|-----------|----------|
| temp=0.1 | 7 | 7 | 100% | 8.71 |
| temp=0.5 | 7 | 7 | 100% | 9.57 |
| temp=1.0 | 7 | 7 | 100% | 9.14 |

---

## Rubric

- 10 = fully correct and complete answer
- 7–9 = mostly correct, minor missing details
- 4–6 = partially correct, missing key concepts
- 1–3 = incorrect but related
- 0 = irrelevant or unsafe output

The rubric evaluates semantic correctness, not wording or style differences.

---

## Verdict

Best configuration: **temperature = 0.5**

### Why:
- It achieved the highest average score (9.57)
- It maintained 100% pass rate like other configurations
- It produced the most balanced answers (accuracy + completeness)

### Observations:
- Temperature 0.1 is too deterministic → slightly less expressive answers
- Temperature 0.5 is optimal → best balance of stability and detail
- Temperature 1.0 introduces more randomness but does not improve quality

### Judge reliability:
The LLM judge is generally reliable for semantic evaluation, but:
- It may slightly overestimate simple correct answers
- It cannot perfectly detect depth differences in explanations

Overall, the evaluation is trustworthy for comparative benchmarking, especially for temperature tuning.