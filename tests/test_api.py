from unittest.mock import patch
from io import BytesIO

import openpyxl
from django.urls import reverse
from rest_framework.test import APITestCase
from accounts.models import User
from lessons.models import LessonSession, UserSession
from goals.models import Goal, KIInteraction
from reflections.models import Reflection

class GroupPermissionTests(APITestCase):
    def setUp(self):
        self.lesson = LessonSession.objects.create(date="2024-01-01", use_ai=True)
        self.user_kg = User.objects.create_user(pseudonym="kg", gruppe=User.KG)
        self.user_vg = User.objects.create_user(pseudonym="vg", gruppe=User.VG)
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
        self.lesson = LessonSession.objects.create(date="2024-01-01", use_ai=True)
        self.user = User.objects.create_user(pseudonym="vg", gruppe=User.VG)
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


class ExportTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            pseudonym="staff", password="pw", is_staff=True
        )
        self.regular = User.objects.create_user(pseudonym="regular", password="pw")
        self.lesson1 = LessonSession.objects.create(date="2024-01-01")
        self.lesson2 = LessonSession.objects.create(date="2024-05-01")
        self.user_vg = User.objects.create_user(
            pseudonym="u1", gruppe=User.VG, klassengruppe="10A"
        )
        self.user_kg = User.objects.create_user(
            pseudonym="u2", gruppe=User.KG, klassengruppe="10B"
        )
        self.session1 = UserSession.objects.create(
            user=self.user_vg, lesson_session=self.lesson1
        )
        self.session2 = UserSession.objects.create(
            user=self.user_vg, lesson_session=self.lesson2
        )
        self.session3 = UserSession.objects.create(
            user=self.user_kg, lesson_session=self.lesson1
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
        self.lesson = LessonSession.objects.create(date="2024-01-01", use_ai=True)
        self.user_vg = User.objects.create_user(pseudonym="vg", gruppe=User.VG)
        self.user_kg = User.objects.create_user(pseudonym="kg", gruppe=User.KG)
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
