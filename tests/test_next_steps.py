from unittest.mock import patch

from rest_framework.test import APITestCase

from accounts.models import User
from lessons.models import LessonSession, UserSession
from goals.models import Goal
from reflections.models import Reflection


class NextStepSuggestTests(APITestCase):
    def setUp(self):
        self.lesson = LessonSession.objects.create(date="2024-01-01")
        self.user = User.objects.create_user(pseudonym="vg", gruppe=User.VG)
        self.session = UserSession.objects.create(user=self.user, lesson_session=self.lesson)
        self.goal = Goal.objects.create(
            user_session=self.session, raw_text="Test", final_text="Test"
        )

    def test_endpoint_returns_suggestions(self):
        self.client.force_login(self.user)
        with patch("reflections.views.suggest_next_steps", return_value=["A", "B"]) as mock:
            resp = self.client.post(
                "/api/vg/next-step/suggest/",
                {"goal_id": str(self.goal.id), "obstacles": "keine"},
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["suggestions"], ["A", "B"])
        mock.assert_called_once_with(self.goal, "keine")

    def test_selection_creates_reflection(self):
        self.client.force_login(self.user)
        payload = {
            "goal_id": str(self.goal.id),
            "user_session": str(self.session.id),
            "result": "yes",
            "obstacles": "Zeitmangel",
            "selected": "Weiter üben",
        }
        resp = self.client.post("/api/vg/next-step/suggest/", payload)
        self.assertEqual(resp.status_code, 201)
        ref = Reflection.objects.get(goal=self.goal)
        self.assertEqual(ref.next_step, "Weiter üben")
        self.assertEqual(ref.next_step_source, "ai")

