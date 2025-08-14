import json
import os
from unittest.mock import patch

from django.test import TestCase

from config.models import SiteSettings
from goals import services


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


class OpenAIKeyTests(TestCase):
    def setUp(self):
        self.payload = {
            "specific": True,
            "measurable": True,
            "achievable": True,
            "relevant": True,
            "time_bound": True,
            "question": "",
        }
        self.addCleanup(lambda: os.environ.pop("OPENAI_API_KEY", None))

    @patch("goals.services.OpenAI")
    def test_env_fallback_when_no_db_key(self, mock_openai):
        os.environ["OPENAI_API_KEY"] = "env-key"
        mock_openai.return_value = DummyClient(self.payload)
        services.evaluate_smart("Ziel", "Mathe")
        assert mock_openai.call_args.kwargs["api_key"] == "env-key"

    @patch("goals.services.OpenAI")
    def test_use_site_settings_key(self, mock_openai):
        settings = SiteSettings.get()
        settings.openai_api_key = "db-key"
        settings.save()
        mock_openai.return_value = DummyClient(self.payload)
        services.evaluate_smart("Ziel", "Mathe")
        assert mock_openai.call_args.kwargs["api_key"] == "db-key"
