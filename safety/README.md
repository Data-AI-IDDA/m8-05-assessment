# Safety Mitigation

## What I added
Prompt-injection guardrail in `llm_service._guard_input()`.

A regex pattern list checks every user message before it reaches the model.
Phrases like "ignore your instructions", "reveal your prompt", "you are now",
"pretend to be", and "jailbreak" are matched case-insensitively.
If matched, the model is never called — a hardcoded refusal is returned instead.

A second check in `_guard_output()` ensures the model response never echoes
the system prompt or outputs a bare "HACKED" string.

## Before / after example

**Attack input:** 