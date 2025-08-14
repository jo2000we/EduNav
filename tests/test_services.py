import json
import pytest
from goals.services import evaluate_smart, suggest_next_steps, AiCoach
from goals.models import Goal, KIInteraction, OverallGoal
from lessons.models import Classroom, LessonSession, UserSession
from accounts.models import User


class DummyClient:
    class Responses:
        def __init__(self, payload):
            self.payload = payload

        def create(self, *args, **kwargs):
            class Resp:
                def __init__(self, payload):
                    self.output = [
                        type('obj', (), {
                            'content': [type('obj', (), {'text': json.dumps(payload)})]
                        })
                    ]
            return Resp(self.payload)

    def __init__(self, payload):
        self.responses = self.Responses(payload)


class DummyTextClient:
    class Responses:
        def __init__(self, text):
            self.text = text

        def create(self, *args, **kwargs):
            class Resp:
                def __init__(self, text):
                    self.output = [
                        type('obj', (), {
                            'content': [type('obj', (), {'text': text})]
                        })
                    ]
            return Resp(self.text)

    def __init__(self, text):
        self.responses = self.Responses(text)


def test_evaluate_smart_llm_parsing():
    payload = {
        "specific": True,
        "measurable": False,
        "achievable": True,
        "relevant": True,
        "time_bound": False,
        "question": "Wie kannst du dein Ziel messbar machen?",
    }
    client = DummyClient(payload)
    result = evaluate_smart("Ich möchte besser rechnen", "Mathe", client=client)
    assert result["overall"] == 3
    assert result["question"] == "Wie kannst du dein Ziel messbar machen?"
    assert result["measurable"] is False


def test_suggest_next_steps_parsing():
    class G:
        final_text = "Bruchrechnen"
        raw_text = "Bruchrechnen"

    text = (
        "- Eins zwei drei vier fünf sechs sieben acht neun zehn elf zwölf dreizehn\n"
        "- Zweiter Vorschlag\n"
        "- Dritter Vorschlag\n"
        "- Vierter Vorschlag"
    )
    client = DummyTextClient(text)
    suggestions = suggest_next_steps(G(), "keine", client=client)
    assert len(suggestions) == 3
    assert suggestions[0].split()[-1] == "zwölf"
    assert all(len(s.split()) <= 12 for s in suggestions)


@pytest.mark.django_db
def test_conversation_includes_history_and_overall_goal():
    classroom = Classroom.objects.create(name="10A", use_ai=True)
    lesson = LessonSession.objects.create(date="2024-01-01", classroom=classroom)
    user = User.objects.create_user(pseudonym="alice", gruppe=User.VG, classroom=classroom)
    session = UserSession.objects.create(user=user, lesson_session=lesson)
    past_goal = Goal.objects.create(user_session=session, raw_text="Alt", final_text="Älteres Ziel")
    OverallGoal.objects.create(user=user, text="Langfristig Mathe")
    goal = Goal.objects.create(user_session=session, raw_text="Neu")
    KIInteraction.objects.create(goal=goal, turn=1, role="user", content="Neu")
    coach = AiCoach()
    convo = coach._conversation(goal)
    assert "Langfristig Mathe" in convo
    assert "Älteres Ziel" in convo
