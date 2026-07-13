# Safety & Mitigations

We implemented two primary safety mitigations in `llm_service.py`:

## 1. Heuristic Prompt Injection Defense
We added a `_guard_input()` method that intercepts user text before it ever reaches the LLM. It checks the text against a list of known jailbreak vectors (e.g., "ignore all previous instructions", "system prompt").
* **Before:** The LLM might break character and reveal its system instructions.
* **After:** The backend short-circuits and returns a fast, deterministic block message: `🛡️ Safety Guardrail Triggered`.

## 2. Strict Scope Enforcement
In `SYSTEM_PROMPT`, we explicitly command the model to refuse non-programming queries.
* **Before:** A user could turn the coding assistant into a free creative writing tool or recipe generator, wasting tokens and violating product scope.
* **After:** If the user asks for a cookie recipe, the model safely responds: *"I apologize, but as a Python Code Explainer, I can only assist with programming, computer science, or technology-related questions."*