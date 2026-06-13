"""
safety/guardrail.py — Input safety pre-filter
Runs before every LLM call. Three-pass check:
  1. Prompt injection / system override attempts
  2. Requests for harmful or malicious content
  3. Clearly off-topic subject matter
"""

import re
from typing import TypedDict


class SafetyResult(TypedDict):
    safe:   bool
    reason: str


# ─────────────────────────────────────────────────────
# Pass 1 — Prompt injection / system override patterns
# Attempts to change the assistant's role or leak its instructions.
# ─────────────────────────────────────────────────────
INJECTION_PATTERNS: list[str] = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"forget\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"disregard\s+(all\s+)?(previous|prior|above)",
    r"you\s+are\s+now\s+(dan|jailbreak|unrestricted|free|evil|unfiltered)",
    r"act\s+as\s+(if\s+you\s+(have|had)\s+no\s+)?(dan|an?\s+unrestricted|evil)",
    r"pretend\s+(you\s+have\s+no|there\s+are\s+no)\s+(rules|restrictions|guidelines|limits)",
    r"override\s+(your\s+)?(system\s+)?(prompt|instructions?|rules?)",
    r"new\s+instructions?\s*:",
    r"system\s*prompt\s*:",
    r"<\s*system\s*>",
    r"\[\s*system\s*\]",
    r"reveal\s+(your\s+)?(system\s+)?(prompt|instructions?|rules?)",
    r"what\s+are\s+your\s+(system\s+)?(prompt|instructions?|rules?)",
    r"show\s+me\s+your\s+(system\s+)?(prompt|instructions?)",
    r"\bjailbreak\b",
    r"\bdo\s+anything\s+now\b",
    r"developer\s+mode\s+(enabled|on|activated)",
    r"you\s+have\s+no\s+(rules|restrictions|guidelines|limits)",
]

# ─────────────────────────────────────────────────────
# Pass 2 — Harmful content patterns
# Requests for malicious code, exploits, or hacking scripts.
# ─────────────────────────────────────────────────────
HARMFUL_PATTERNS: list[str] = [
    r"\b(write|create|make|build|generate|code|program)\s+(me\s+)?(a\s+)?"
    r"(virus|malware|ransomware|trojan|keylogger|rootkit|spyware|worm|botnet)\b",
    r"\b(hack|exploit|crack|break\s+into|bypass)\s+(a\s+|the\s+|into\s+)?"
    r"(password|system|server|database|account|network|website)\b",
    r"\b(steal|dump|exfiltrate|extract)\s+.{0,30}(password|credential|data|token)\b",
    r"\bsql\s+injection\b.{0,60}\b(attack|exploit|payload|bypass)\b",
    r"\b(reverse\s+shell|bind\s+shell|shell\s+code|shellcode)\b",
    r"\b(privilege\s+escalation|privesc)\b",
    r"\bwrite\s+(me\s+)?a\s+(python\s+)?(script|code|program)\s+to\s+"
    r"(hack|crack|steal|bypass|exploit)\b",
]

# ─────────────────────────────────────────────────────
# Pass 3 — Off-topic keyword filter
# Catches subjects clearly outside the AI/ML course scope.
# Each entry is a plain substring (lowercased match).
# ─────────────────────────────────────────────────────
OFF_TOPIC_KEYWORDS: list[str] = [
    "recipe",
    "cook",
    "cooking",
    "bake",
    "baking",
    "politics",
    "political party",
    "election",
    "relationship",
    "dating",
    "romance",
    "stock price",
    "stock market",
    "crypto",
    "cryptocurrency",
    "bitcoin",
    "ethereum",
    "forex",
    "sports score",
    "football match",
    "basketball game",
    "celebrity gossip",
    "horoscope",
    "love",
]


def check_input_safety(user_input: str) -> SafetyResult:
    """
    Check a user message in three passes before sending it to the LLM.

    Pass 1 — Injection detection:
        Regex patterns for system-prompt override or leak attempts.

    Pass 2 — Harmful content detection:
        Regex patterns for malicious code or exploit requests.

    Pass 3 — Off-topic keyword check:
        Plain substring match against subjects outside the AI/ML curriculum.

    Returns SafetyResult(safe=True) only when all three passes clear.
    """
    text = user_input.lower().strip()

    # ── Pass 1: injection ────────────────────────────
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return SafetyResult(
                safe=False,
                reason=(
                    "Attempted prompt injection or system override detected. "
                    "I cannot change my instructions or role."
                ),
            )

    # ── Pass 2: harmful content ──────────────────────
    for pattern in HARMFUL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return SafetyResult(
                safe=False,
                reason=(
                    "Request flagged for potentially harmful content. "
                    "I'm StudyBuddy — I only assist with AI/ML topics, "
                    "not malicious code or hacking."
                ),
            )

    # ── Pass 3: off-topic keywords ───────────────────
    for keyword in OFF_TOPIC_KEYWORDS:
        if keyword in text:
            return SafetyResult(
                safe=False,
                reason=(
                    f"That topic ('{keyword}') is outside my scope. "
                    "I'm StudyBuddy — I only help with AI/ML topics. "
                    "Please ask something from your AI/ML curriculum!"
                ),
            )

    return SafetyResult(safe=True, reason="")