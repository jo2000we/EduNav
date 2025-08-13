import json
from goals.services import evaluate_smart


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
