from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from lessons.models import LessonSession, UserSession, Classroom
from goals.models import Goal
from reflections.models import Reflection


class DashboardHistoryTests(TestCase):
    def setUp(self):
        self.classroom = Classroom.objects.create(name="10A", use_ai=True)
        self.user = User.objects.create_user(pseudonym="u1", gruppe=User.VG, classroom=self.classroom)
        self.client.force_login(self.user)

    def test_history_in_context(self):
        past_lesson = LessonSession.objects.create(date="2024-01-01", classroom=self.classroom)
        past_session = UserSession.objects.create(user=self.user, lesson_session=past_lesson)
        goal = Goal.objects.create(user_session=past_session, raw_text="lorem", final_text="lorem", smart_score={"overall": 4})
        Reflection.objects.create(user_session=past_session, goal=goal, result="yes", obstacles="", next_step="")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("goals", response.context)
        goals = response.context["goals"]
        self.assertTrue(any(g.id == goal.id for g in goals))
        self.assertEqual(goals[0].reflection_set.first().result, "yes")
