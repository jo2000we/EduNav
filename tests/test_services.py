import json
from goals.services import evaluate_smart, suggest_next_steps


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
    assert result["score"] == 3
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
