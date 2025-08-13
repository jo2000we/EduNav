from django.urls import reverse
from rest_framework.test import APITestCase
from accounts.models import User
from lessons.models import LessonSession, UserSession
from goals.models import Goal, KIInteraction

class GroupPermissionTests(APITestCase):
    def setUp(self):
        self.lesson = LessonSession.objects.create(date="2024-01-01")
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
