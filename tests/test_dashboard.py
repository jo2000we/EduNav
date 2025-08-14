from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from lessons.models import LessonSession, UserSession, Classroom
from goals.models import Goal, OverallGoal
from reflections.models import Reflection
from config.models import SiteSettings


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


class DashboardAiToggleTests(TestCase):
    def setUp(self):
        self.classroom = Classroom.objects.create(name="10A", use_ai=True)
        self.user = User.objects.create_user(
            pseudonym="u1", gruppe=User.VG, classroom=self.classroom
        )
        self.client.force_login(self.user)

    def test_ai_buttons_hidden_when_disabled(self):
        settings = SiteSettings.get()
        settings.allow_ai = False
        settings.save()
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["can_use_ai"])
        self.assertNotIn("Reflexion starten", response.content.decode())


class DashboardOverallGoalTests(TestCase):
    def setUp(self):
        self.classroom = Classroom.objects.create(name="10A")
        self.user = User.objects.create_user(pseudonym="u1", classroom=self.classroom)
        self.client.force_login(self.user)

    def test_overall_goal_displayed(self):
        OverallGoal.objects.create(user=self.user, text="Langfristig")
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Langfristig")
        self.assertContains(response, reverse("overall_goal"))

    def test_overall_goal_update_reflected_on_dashboard(self):
        OverallGoal.objects.create(user=self.user, text="Alt")
        self.client.post("/api/overall-goal/", {"text": "Neu"})
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Neu")
