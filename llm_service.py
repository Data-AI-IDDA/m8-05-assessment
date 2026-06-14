"""
Backend for the LLM chat micro-service.

Phase 1:
- Connects to a local Ollama model
- Maintains conversation history
- Uses a system prompt
- Returns responses

Token tracking, safety, and streaming will be added later.
"""

from __future__ import annotations

import os
from ollama import Client


SYSTEM_PROMPT = """You are a Data and AI Study Buddy.

Your purpose is to help users learn topics related to:
- Artificial Intelligence
- Machine Learning
- Data Science
- Python programming
- Prompt Engineering
- Large Language Models

Be accurate, concise, and educational.
"""


class ChatService:
    """Holds conversation state and talks to the model."""

    def __init__(self, model: str | None = None, temperature: float = 0.4) -> None:
        self.model = model or os.environ.get("MODEL", "qwen2.5:3b")
        self.temperature = temperature

        self.client = Client(host="http://localhost:11434")

        self.history: list[dict[str, str]] = []

        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def reset(self) -> None:
        self.history = []

    
    def _classify_request(self, user_text: str) -> bool:
        """
        Returns True if the request is related to Data/AI/Python,
        False otherwise.
        """

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": """
        You are a binary classifier.

        Determine whether the user's request is related to any of these topics:

        - Artificial Intelligence
        - Machine Learning
        - Deep Learning
        - Data Science
        - Python programming
        - Software development
        - Prompt Engineering
        - Large Language Models
        - Statistics
        - SQL
        - Algorithms

        Reply with EXACTLY one word:

        YES

        or

        NO

        Do not explain your answer.
        Do not output punctuation.
        Do not output anything else.
        """,
                },
                {
                    "role": "user",
                    "content": user_text,
                },
            ],
            options={
                "temperature": 0,
            },
        )

        answer = response["message"]["content"].strip().upper()

        return "NO" not in answer

    def _guard_input(self, user_text: str) -> str | None:

        text = user_text.lower()

        injection_patterns = [
            "ignore previous instructions",
            "ignore all previous instructions",
            "forget your system prompt",
            "developer mode",
            "jailbreak",
        ]

        if any(pattern in text for pattern in injection_patterns):
            return (
                "Sorry, I can't ignore or override my system instructions."
            )

        if not self._classify_request(user_text):
            return (
                "I'm a Data + AI Study Buddy. "
                "Please ask a question related to AI, Machine Learning, "
                "Data Science, Python, or programming."
            )

        return None

    def _guard_output(self, model_text: str) -> str:
        return model_text

    def send(self, user_text: str) -> str:
        blocked = self._guard_input(user_text)
        if blocked is not None:
            return blocked

        self.history.append(
            {
                "role": "user",
                "content": user_text,
            }
        )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ] + self.history

        response = self.client.chat(
            model=self.model,
            messages=messages,
            options={
                "temperature": self.temperature,
            },
        )

        reply = response["message"]["content"]

        reply = self._guard_output(reply)

        self.history.append(
            {
                "role": "assistant",
                "content": reply,
            }
        )

        return reply

    def stream(self, user_text: str):
        """Stream the model's response token by token."""

        blocked = self._guard_input(user_text)
        if blocked is not None:
            yield blocked
            return

        self.history.append(
            {
                "role": "user",
                "content": user_text,
            }
        )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ] + self.history

        stream = self.client.chat(
            model=self.model,
            messages=messages,
            stream=True,
            options={
                "temperature": self.temperature,
            },
        )

        full_reply = ""

        last_chunk = None

        for chunk in stream:
            last_chunk = chunk
            text = chunk["message"]["content"]
            full_reply += text
            yield text
        
        self.total_input_tokens += last_chunk.prompt_eval_count or 0
        self.total_output_tokens += last_chunk.eval_count or 0

        full_reply = self._guard_output(full_reply)

        self.history.append(
            {
                "role": "assistant",
                "content": full_reply,
            }
        )