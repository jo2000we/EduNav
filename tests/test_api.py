from unittest.mock import patch
from io import BytesIO

import openpyxl
from django.urls import reverse
from rest_framework.test import APITestCase
from accounts.models import User
from lessons.models import LessonSession, UserSession, Classroom
from goals.models import Goal, KIInteraction, OverallGoal
from reflections.models import Reflection

class GroupPermissionTests(APITestCase):
    def setUp(self):
        self.classroom = Classroom.objects.create(name="10A", use_ai=True)
        self.lesson = LessonSession.objects.create(date="2024-01-01", classroom=self.classroom)
        self.user_kg = User.objects.create_user(pseudonym="kg", gruppe=User.KG, classroom=self.classroom)
        self.user_vg = User.objects.create_user(pseudonym="vg", gruppe=User.VG, classroom=self.classroom)
        self.session_kg = UserSession.objects.create(user=self.user_kg, lesson_session=self.lesson)
        self.session_vg = UserSession.objects.create(user=self.user_vg, lesson_session=self.lesson)

    def test_kg_cannot_access_vg_endpoint(self):
        self.client.force_login(self.user_kg)
        resp = self.client.post("/api/vg/goals/", {"user_session": str(self.session_kg.id), "raw_text": "test"})
        self.assertEqual(resp.status_code, 403)

    def test_vg_goal_creates_interaction(self):
        self.client.force_login(self.user_vg)
        resp = self.client.post("/api/vg/goals/", {"user_session": str(self.session_vg.id), "raw_text": "Ich schreibe 3 Fragen"})
        self.assertEqual(resp.status_code, 201)
        goal_id = resp.data["id"]
        goal = Goal.objects.get(id=goal_id)
        self.assertEqual(goal.interactions.count(), 1)


class GoalFinalizeTests(APITestCase):
    def setUp(self):
        self.classroom = Classroom.objects.create(name="10A", use_ai=True)
        self.lesson = LessonSession.objects.create(date="2024-01-01", classroom=self.classroom)
        self.user = User.objects.create_user(pseudonym="vg", gruppe=User.VG, classroom=self.classroom)
        self.session = UserSession.objects.create(user=self.user, lesson_session=self.lesson)
        self.client.force_login(self.user)
        resp = self.client.post(
            "/api/vg/goals/", {"user_session": str(self.session.id), "raw_text": "erstes"}
        )
        self.goal = Goal.objects.get(id=resp.data["id"])

    @patch("goals.views.AiCoach.finalize", return_value="Finales Ziel")
    def test_goal_finalize_creates_interaction_and_final_text(self, mock_final):
        resp = self.client.post("/api/vg/goals/finalize/", {"goal_id": str(self.goal.id)})
        self.assertEqual(resp.status_code, 200)
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.final_text, "Finales Ziel")
        self.assertEqual(self.goal.interactions.count(), 2)
        last = self.goal.interactions.last()
        self.assertEqual(last.role, "assistant")
        self.assertEqual(last.content, "Finales Ziel")


class AiCoachPromptTests(APITestCase):
    def setUp(self):
        self.classroom = Classroom.objects.create(name="10A", use_ai=True)
        self.lesson = LessonSession.objects.create(date="2024-01-01", classroom=self.classroom)
        self.user = User.objects.create_user(pseudonym="vg", gruppe=User.VG, classroom=self.classroom)
        self.session = UserSession.objects.create(user=self.user, lesson_session=self.lesson)
        OverallGoal.objects.create(user=self.user, text="Langfristig Mathe")
        Goal.objects.create(user_session=self.session, raw_text="Alt", final_text="Älteres Ziel")
        self.client.force_login(self.user)
        resp = self.client.post(
            "/api/vg/goals/", {"user_session": str(self.session.id), "raw_text": "Neu"}
        )
        self.goal = Goal.objects.get(id=resp.data["id"])

    @patch("goals.views.evaluate_smart")
    @patch("goals.services.AiCoach.ask")
    def test_prompt_contains_history(self, mock_ask, mock_eval):
        mock_eval.return_value = {
            "specific": True,
            "measurable": True,
            "achievable": True,
            "relevant": True,
            "time_bound": True,
            "score": 5,
            "question": "",
        }
        mock_ask.return_value = "Final"
        resp = self.client.post(
            "/api/vg/coach/next/", {"goal_id": str(self.goal.id), "user_reply": "Antwort"}
        )
        self.assertEqual(resp.status_code, 200)
        prompt = mock_ask.call_args[0][0]
        self.assertIn("Langfristig Mathe", prompt)
        self.assertIn("Älteres Ziel", prompt)


class ExportTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            pseudonym="staff", password="pw", is_staff=True
        )
        self.regular = User.objects.create_user(pseudonym="regular", password="pw")
        self.class_a = Classroom.objects.create(name="10A")
        self.class_b = Classroom.objects.create(name="10B")
        self.lesson1 = LessonSession.objects.create(date="2024-01-01", classroom=self.class_a)
        self.lesson2 = LessonSession.objects.create(date="2024-05-01", classroom=self.class_a)
        self.lesson3 = LessonSession.objects.create(date="2024-01-01", classroom=self.class_b)
        self.user_vg = User.objects.create_user(
            pseudonym="u1", gruppe=User.VG, classroom=self.class_a
        )
        self.user_kg = User.objects.create_user(
            pseudonym="u2", gruppe=User.KG, classroom=self.class_b
        )
        self.session1 = UserSession.objects.create(
            user=self.user_vg, lesson_session=self.lesson1
        )
        self.session2 = UserSession.objects.create(
            user=self.user_vg, lesson_session=self.lesson2
        )
        self.session3 = UserSession.objects.create(
            user=self.user_kg, lesson_session=self.lesson3
        )
        Goal.objects.create(user_session=self.session1, raw_text="g1")
        Goal.objects.create(user_session=self.session2, raw_text="g2")
        Goal.objects.create(user_session=self.session3, raw_text="g3")

    def test_non_staff_export_forbidden(self):
        self.client.force_login(self.regular)
        resp = self.client.get("/api/export/csv/")
        self.assertEqual(resp.status_code, 302)
        resp = self.client.get("/api/export/xlsx/")
        self.assertEqual(resp.status_code, 302)

    def test_staff_can_export_with_filters(self):
        self.client.force_login(self.staff)
        params = {"from": "2024-02-01", "class": "10A", "group": "VG"}
        resp = self.client.get("/api/export/csv/", params)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn("g2", content)
        self.assertNotIn("g1", content)
        self.assertNotIn("g3", content)
        resp = self.client.get("/api/export/xlsx/", params)
        self.assertEqual(resp.status_code, 200)
        wb = openpyxl.load_workbook(BytesIO(resp.content))
        ws = wb["flat_dataset"]
        rows = list(ws.iter_rows(values_only=True))
        header = rows[0]
        idx = header.index("goal_raw")
        values = [r[idx] for r in rows[1:]]
        self.assertEqual(values, ["g2"])


class NextStepSuggestAPITests(APITestCase):
    def setUp(self):
        self.classroom = Classroom.objects.create(name="10A", use_ai=True)
        self.lesson = LessonSession.objects.create(date="2024-01-01", classroom=self.classroom)
        self.user_vg = User.objects.create_user(pseudonym="vg", gruppe=User.VG, classroom=self.classroom)
        self.user_kg = User.objects.create_user(pseudonym="kg", gruppe=User.KG, classroom=self.classroom)
        self.session_vg = UserSession.objects.create(
            user=self.user_vg, lesson_session=self.lesson
        )
        self.session_kg = UserSession.objects.create(
            user=self.user_kg, lesson_session=self.lesson
        )
        self.goal_vg = Goal.objects.create(
            user_session=self.session_vg, raw_text="Test", final_text="Test"
        )
        self.goal_kg = Goal.objects.create(
            user_session=self.session_kg, raw_text="Test", final_text="Test"
        )

    def test_ai_selection_creates_reflection(self):
        self.client.force_login(self.user_vg)
        payload = {
            "goal_id": str(self.goal_vg.id),
            "user_session": str(self.session_vg.id),
            "result": "yes",
            "obstacles": "keine",
            "selected": "Weiter üben",
        }
        resp = self.client.post("/api/vg/next-step/suggest/", payload)
        self.assertEqual(resp.status_code, 201)
        ref = Reflection.objects.get(goal=self.goal_vg)
        self.assertEqual(ref.next_step, "Weiter üben")
        self.assertEqual(ref.next_step_source, "ai")

    def test_kg_cannot_access_suggest_endpoint(self):
        self.client.force_login(self.user_kg)
        resp = self.client.post(
            "/api/vg/next-step/suggest/", {"goal_id": str(self.goal_kg.id)}
        )
        self.assertEqual(resp.status_code, 403)


class LoginWorkflowTests(APITestCase):
    def setUp(self):
        self.classroom = Classroom.objects.create(name="10A", code="abc", use_ai=True)
        self.alice = User.objects.create_user(pseudonym="alice")
        self.bob = User.objects.create_user(pseudonym="bob")

    def test_login_assigns_classroom(self):
        resp = self.client.post(
            "/api/login/", {"pseudonym": "alice", "class_code": "abc"}, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.classroom, self.classroom)

    def test_login_missing_classroom(self):
        resp = self.client.post(
            "/api/login/", {"pseudonym": "bob", "class_code": "wrong"}, format="json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_login_unknown_user(self):
        resp = self.client.post(
            "/api/login/", {"pseudonym": "unknown"}, format="json"
        )
        self.assertEqual(resp.status_code, 400)
