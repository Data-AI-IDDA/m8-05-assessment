"""
safety/guardrail.py
--------------------
Concrete safety mitigation for the Study Buddy assistant.

Two layers, both demonstrated in safety/README.md:

1. INPUT guardrail (`check_input`)
   - Detects classic prompt-injection patterns: "ignore previous
     instructions", "you are now...", "reveal your system prompt",
     "act as", "pretend you have no rules", etc.
   - Detects out-of-scope requests using a simple keyword/topic check
     against an allow-list of course topics (best-effort heuristic, not
     a full classifier — documented as a known limitation in
     safety/README.md).
   - On a hit, the user's raw message is NEVER forwarded to the model.
     We return a canned, safe refusal instead. This is the core
     mitigation: untrusted text is treated as data, not as instructions,
     and never reaches the LLM call when it looks like an injection
     attempt.

2. OUTPUT guardrail (`check_output`)
   - A defense-in-depth backstop: scans the model's own reply for
     patterns that look like it leaked the system prompt verbatim, or
     that look like a fabricated API key / secret / PII pattern (e.g.
     "sk-...", long hex/base64 blobs labeled as a key, email+SSN-like
     strings). If found, the reply is replaced with a safe message
     rather than shown to the user.

Both functions return a `GuardrailResult` so the caller (llm_service.py)
can decide what to do and log why.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# --------------------------------------------------------------------------
# Patterns
# --------------------------------------------------------------------------

INJECTION_PATTERNS = [
    r"ignore (all|any|the) (previous|prior|above) instructions",
    r"disregard (all|any|the) (previous|prior|above) (instructions|rules)",
    r"you are now\s+\w+",
    r"forget (your|all) (rules|instructions|system prompt)",
    r"reveal (your|the) system prompt",
    r"show me (your|the) system prompt",
    r"what (is|are) your (system|hidden) (prompt|instructions)",
    r"pretend (you|that you) (have no|don't have any) (rules|restrictions)",
    r"act as (an?|the) .*(no rules|unfiltered|jailbroken|dan)",
    r"\bdan mode\b",
    r"developer mode",
    r"repeat (the|your) (words|text|instructions) above",
    r"print (your|the) (initial|system) prompt",
]

# Topics this assistant is allowed to discuss. Kept intentionally small
# and explicit, matching the course syllabus referenced in the system
# prompt. This is a heuristic allow-list, not a semantic classifier — see
# safety/README.md for the documented limitation and false-positive risk.
ON_TOPIC_KEYWORDS = [
    "python", "pandas", "numpy", "function", "loop", "variable", "list",
    "dictionary", "class", "module", "package", "pip", "venv",
    "llm", "prompt", "prompting", "token", "temperature", "top_p", "top-p",
    "sampling", "system prompt", "few-shot", "zero-shot", "chain of thought",
    "structured output", "json schema", "function calling", "tool use",
    "ollama", "gemini", "openai", "anthropic", "claude", "hosted model",
    "local model", "fine-tun", "embedding", "vector", "rag", "retrieval",
    "evaluation", "eval", "benchmark", "rubric", "pass rate", "judge",
    "safety", "guardrail", "injection", "jailbreak", "pii", "hallucinat",
    "streamlit", "chat", "conversation", "context window", "latency",
    "api", "rate limit", "cost", "inference", "model", "ai", "ml",
    "machine learning", "neural network", "transformer", "bootcamp",
    "course", "assignment", "assessment", "study", "quiz", "exam",
]

# A short list of clearly off-topic categories we explicitly want to
# decline, used only to make the refusal message feel natural — the
# actual gate is the allow-list keyword check below.
OFF_TOPIC_HINTS = [
    "recipe", "weather", "stock price", "horoscope", "celebrity",
    "relationship advice", "medical advice", "legal advice", "diagnose",
    "current news", "sports score", "lottery", "dating",
]

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",          # OpenAI-style key
    r"AIza[0-9A-Za-z\-_]{20,}",       # Google API key style
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"\b\d{3}-\d{2}-\d{4}\b",          # SSN-like pattern
]

SYSTEM_PROMPT_LEAK_MARKER = "Study Buddy\", a focused teaching assistant"


@dataclass
class GuardrailResult:
    blocked: bool
    reason: Optional[str] = None
    safe_reply: Optional[str] = None


# --------------------------------------------------------------------------
# Input guardrail
# --------------------------------------------------------------------------

def _looks_like_injection(text: str) -> Optional[str]:
    lowered = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            return pattern
    return None


def _looks_off_topic(text: str) -> bool:
    lowered = text.lower()
    # If it clearly mentions an on-topic keyword, treat it as in-scope
    # even if it also contains a casual word from OFF_TOPIC_HINTS.
    if any(kw in lowered for kw in ON_TOPIC_KEYWORDS):
        return False
    # Otherwise, if it's a short/clear request matching an off-topic
    # hint, flag it. We deliberately do NOT block on every message with
    # zero keyword matches (e.g. "thanks!", "ok continue") — only when
    # it also looks like a real standalone question (longer than a few
    # words and phrased as a request/question).
    is_question_like = bool(re.search(r"\?|^(what|how|why|tell me|give me|write|recommend|plan)\b", lowered.strip()))
    has_off_topic_hint = any(hint in lowered for hint in OFF_TOPIC_HINTS)
    if has_off_topic_hint and is_question_like:
        return True
    # Heuristic: a fairly long question with NO on-topic keyword at all
    # is also likely off-topic for this narrow assistant.
    if is_question_like and len(lowered.split()) >= 6:
        return True
    return False


def check_input(user_message: str) -> GuardrailResult:
    injection_hit = _looks_like_injection(user_message)
    if injection_hit:
        return GuardrailResult(
            blocked=True,
            reason=f"prompt_injection_pattern:{injection_hit}",
            safe_reply=(
                "I can't follow instructions embedded in a message that try "
                "to change my role or reveal internal configuration. I'm "
                "happy to keep helping with course topics — Python, "
                "prompting, model choice, evaluation, or safety — what "
                "would you like to go over?"
            ),
        )

    if _looks_off_topic(user_message):
        return GuardrailResult(
            blocked=True,
            reason="out_of_scope_topic",
            safe_reply=(
                "That's outside what I can help with — I'm scoped to this "
                "bootcamp's material (Python, LLM prompting, model choice, "
                "evaluation, and safety/guardrails). Want to ask something "
                "from one of those areas instead?"
            ),
        )

    return GuardrailResult(blocked=False)


# --------------------------------------------------------------------------
# Output guardrail
# --------------------------------------------------------------------------

def check_output(model_reply: str) -> GuardrailResult:
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, model_reply):
            return GuardrailResult(
                blocked=True,
                reason=f"secret_like_pattern:{pattern}",
                safe_reply=(
                    "I caught my own draft reply containing something that "
                    "looked like a secret/key or sensitive identifier, so "
                    "I've withheld it. Could you rephrase what you need?"
                ),
            )

    if SYSTEM_PROMPT_LEAK_MARKER.lower() in model_reply.lower():
        return GuardrailResult(
            blocked=True,
            reason="system_prompt_leak",
            safe_reply=(
                "I won't repeat my internal configuration verbatim. Let me "
                "know what course topic you'd like help with instead."
            ),
        )

    return GuardrailResult(blocked=False)
