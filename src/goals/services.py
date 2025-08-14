from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional, List
import os
from openai import OpenAI, OpenAIError
from .models import Goal, OverallGoal


SMART_PROMPT = (
    "Du bist ein knapper, freundlicher Lerncoach. Du hilfst Schüler:innen, ein SMART-Ziel für die nächste Unterrichtsstunde zu formulieren."
)


def _get_client(api_key: Optional[str] = None) -> Optional[OpenAI]:
    """Return an OpenAI client using SiteSettings or env fallback."""
    if api_key:
        return OpenAI(api_key=api_key)
    key = None
    try:
        from django.apps import apps

        SiteSettings = apps.get_model("config", "SiteSettings")
        key = SiteSettings.get().openai_api_key
    except Exception:  # pragma: no cover - Django not ready
        pass
    if not key:
        key = os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=key) if key else None


def evaluate_smart(text: str, topic: str, client: Optional[OpenAI] = None) -> dict:
    """Bewertet einen Zieltext anhand der SMART-Kriterien über das LLM.

    Gibt zusätzlich eine Rückfrage zurück, falls das Ziel noch nicht SMART ist.
    """
    if client is None:
        client = _get_client()

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
            "overall": 0,
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
            "overall": 0,
            "question": "(Fehler bei KI) Bitte versuche es erneut.",
        }

    for key in ["specific", "measurable", "achievable", "relevant", "time_bound"]:
        data[key] = bool(data.get(key))

    data["overall"] = sum(
        data[k]
        for k in ["specific", "measurable", "achievable", "relevant", "time_bound"]
    )
    data.setdefault("question", "")
    return data


@dataclass
class AiCoach:
    api_key: Optional[str] = None

    def __post_init__(self):
        self.client = _get_client(self.api_key)

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

    def _history(self, goal) -> str:
        user = goal.user_session.user
        previous = (
            Goal.objects.filter(user_session__user=user)
            .exclude(id=goal.id)
            .order_by("-created_at")[:3]
        )
        overall = (
            OverallGoal.objects.filter(user=user)
            .order_by("-created_at")
            .first()
        )
        parts: List[str] = []
        if overall:
            parts.append(f"Langfristiges Ziel: {overall.text}")
        if previous:
            texts = [g.final_text or g.raw_text for g in previous]
            parts.append("Frühere Ziele: " + " | ".join(texts))
        return "\n".join(parts)

    def _conversation(self, goal) -> str:
        history = self._history(goal)
        convo = "\n".join(i.content for i in goal.interactions.order_by("turn"))
        return "\n".join([p for p in [history, convo] if p])

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
        client = _get_client()

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
