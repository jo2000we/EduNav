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

    def _conversation(self, goal) -> str:
        return "\n".join(i.content for i in goal.interactions.order_by("turn"))

    def ask_next(self, goal) -> str:
        score = goal.smart_score or {}
        missing = [c for c in ["specific", "measurable", "achievable", "relevant", "time_bound"] if not score.get(c)]
        conversation = self._conversation(goal)
        if not missing:
            return self.finalize(goal)
        mapping = {
            "specific": "konkreter", "measurable": "messbar", "achievable": "realistisch",
            "relevant": "relevant zum Thema", "time_bound": "zeitlich begrenzt",
        }
        crit = mapping[missing[0]]
        prompt = (
            f"{SMART_PROMPT}\n{conversation}\n"
            f"Frage den Lernenden gezielt, damit das Ziel {crit} wird."
        )
        return self.ask(prompt)

    def finalize(self, goal) -> str:
        score = goal.smart_score or {}
        missing = [
            c
            for c in ["specific", "measurable", "achievable", "relevant", "time_bound"]
            if not score.get(c)
        ]
        conversation = self._conversation(goal)
        mapping = {
            "specific": "konkreter",
            "measurable": "messbarer",
            "achievable": "realistischer",
            "relevant": "relevanter zum Thema",
            "time_bound": "zeitlich klarer",
        }
        if missing:
            miss_text = ", ".join(mapping[c] for c in missing)
            prompt = (
                f"{SMART_PROMPT}\n{conversation}\n"
                "Formuliere daraus ein finales SMART-Ziel in weniger als 25 Wörtern. "
                f"Es soll {miss_text} sein."
            )
        else:
            prompt = (
                f"{SMART_PROMPT}\n{conversation}\n"
                "Formuliere daraus ein finales SMART-Ziel in weniger als 25 Wörtern."
            )
        return self.ask(prompt)
