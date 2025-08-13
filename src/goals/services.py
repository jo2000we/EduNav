from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import re
import os
from openai import OpenAI, OpenAIError


SMART_PROMPT = (
    "Du bist ein knapper, freundlicher Lerncoach. Du hilfst Schüler:innen, ein SMART-Ziel für die nächste Unterrichtsstunde zu formulieren."
)


def evaluate_smart(text: str, topic: str | None = None) -> dict:
    specific = any(word in text.lower() for word in ["funktion", "quiz", "text", "bericht", "test"])
    measurable = bool(re.search(r"\d", text))
    achievable = not any(word in text.lower() for word in ["alles", "fertig", "komplett"])
    relevant = bool(topic and topic.lower() in text.lower()) if topic else True
    time_bound = "heute" in text.lower() or "stunde" in text.lower()
    score = sum([specific, measurable, achievable, relevant, time_bound])
    return {
        "specific": specific,
        "measurable": measurable,
        "achievable": achievable,
        "relevant": relevant,
        "time_bound": time_bound,
        "score": score,
    }


@dataclass
class AiCoach:
    api_key: Optional[str] = None

    def __post_init__(self):
        key = self.api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=key) if key else None

    def ask(self, prompt: str) -> str:
        if not self.client:
            return "(KI nicht verfügbar) Bitte formuliere dein Ziel genauer."
        try:
            resp = self.client.responses.create(
                model="gpt-4o-mini",
                input=prompt,
                max_output_tokens=60,
            )
            return resp.output[0].content[0].text.strip()
        except OpenAIError:
            return "(Fehler bei KI) Bitte versuche es erneut."
