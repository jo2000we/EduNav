from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional, List
import os
from openai import OpenAI, OpenAIError


SMART_PROMPT = (
    "Du bist ein knapper, freundlicher Lerncoach. Du hilfst Schüler:innen, ein SMART-Ziel für die nächste Unterrichtsstunde zu formulieren."
)


def evaluate_smart(text: str, topic: str, client: Optional[OpenAI] = None) -> dict:
    """Bewertet einen Zieltext anhand der SMART-Kriterien über das LLM.

    Gibt zusätzlich eine Rückfrage zurück, falls das Ziel noch nicht SMART ist.
    """
    if client is None:
        key = os.getenv("OPENAI_API_KEY")
        client = OpenAI(api_key=key) if key else None

    prompt = (
        f"{SMART_PROMPT}\n"
        f"Thema der Stunde: {topic}\n"
        f"Zieltext: {text}\n"
        "Bewerte, ob das Ziel spezifisch, messbar, erreichbar, relevant und zeitgebunden ist. "
        "Antworte ausschließlich als JSON mit den Schlüsseln "
        "specific, measurable, achievable, relevant, time_bound und question."
    )

    if not client:
        return {
            "specific": False,
            "measurable": False,
            "achievable": False,
            "relevant": False,
            "time_bound": False,
            "score": 0,
            "question": "(KI nicht verfügbar) Bitte formuliere dein Ziel genauer.",
        }

    try:
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            max_output_tokens=150,
        )
        content = resp.output[0].content[0].text.strip()
        data = json.loads(content)
    except (OpenAIError, ValueError, KeyError):
        return {
            "specific": False,
            "measurable": False,
            "achievable": False,
            "relevant": False,
            "time_bound": False,
            "score": 0,
            "question": "(Fehler bei KI) Bitte versuche es erneut.",
        }

    for key in ["specific", "measurable", "achievable", "relevant", "time_bound"]:
        data[key] = bool(data.get(key))

    data["score"] = sum(
        data[k]
        for k in ["specific", "measurable", "achievable", "relevant", "time_bound"]
    )
    data.setdefault("question", "")
    return data


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

    def finalize(self, goal, topic: str) -> str:
        conversation = self._conversation(goal)
        prompt = (
            f"{SMART_PROMPT}\nThema der Stunde: {topic}\n{conversation}\n"
            "Formuliere daraus ein finales SMART-Ziel in weniger als 25 Wörtern."
        )
        return self.ask(prompt)


def suggest_next_steps(goal, obstacles: str, client: Optional[OpenAI] = None) -> List[str]:
    """Generiert bis zu drei nächste Schritte zu einem Ziel.

    Jeder Schritt enthält höchstens zwölf Wörter. Wenn kein LLM verfügbar ist
    oder ein Fehler auftritt, werden einfache Standardvorschläge zurückgegeben.
    """

    if client is None:
        key = os.getenv("OPENAI_API_KEY")
        client = OpenAI(api_key=key) if key else None

    goal_text = getattr(goal, "final_text", None) or getattr(goal, "raw_text", "")
    prompt = (
        f"{SMART_PROMPT}\n"
        f"Ziel: {goal_text}\n"
        f"Hindernisse: {obstacles}\n"
        "Gib maximal drei Vorschläge für nächste Schritte als Bullet Points. "
        "Jeder Vorschlag höchstens zwölf Wörter."
    )

    def _fallback() -> List[str]:
        return [
            "Frage Lehrkraft nach Rat.",
            "Wiederhole relevante Aufgaben Schritt für Schritt.",
            "Arbeite mit Mitschüler zusammen.",
        ]

    if not client:
        return _fallback()

    try:
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            max_output_tokens=120,
        )
        content = resp.output[0].content[0].text.strip()
    except OpenAIError:
        return _fallback()

    suggestions: List[str] = []
    for line in content.splitlines():
        line = line.strip().lstrip("-*•").strip()
        if not line:
            continue
        words = line.split()
        if len(words) > 12:
            line = " ".join(words[:12])
        suggestions.append(line)
        if len(suggestions) >= 3:
            break

    return suggestions or _fallback()
