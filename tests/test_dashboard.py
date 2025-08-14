from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from lessons.models import LessonSession, UserSession, Classroom
from goals.models import Goal, OverallGoal
from reflections.models import Reflection
from config.models import SiteSettings


class GoalVGPageAccessTests(TestCase):
    def setUp(self):
        self.classroom = Classroom.objects.create(name="10A", use_ai=True)
        self.vg_user = User.objects.create_user(
            pseudonym="vg1", gruppe=User.VG, classroom=self.classroom
        )
        self.kg_user = User.objects.create_user(
            pseudonym="kg1", gruppe=User.KG, classroom=self.classroom
        )

    def test_vg_user_can_access(self):
        self.client.force_login(self.vg_user)
        response = self.client.get(reverse("goal_vg"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("user_session_id", response.context)

    def test_non_vg_user_forbidden(self):
        self.client.force_login(self.kg_user)
        response = self.client.get(reverse("goal_vg"))
        self.assertEqual(response.status_code, 403)

    def test_ai_disabled_forbidden(self):
        settings = SiteSettings.get()
        settings.allow_ai = False
        settings.save()
        self.client.force_login(self.vg_user)
        response = self.client.get(reverse("goal_vg"))
        self.assertEqual(response.status_code, 403)


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

    def test_reflection_button_visible_when_ai_disabled(self):
        settings = SiteSettings.get()
        settings.allow_ai = False
        settings.save()
        lesson = LessonSession.objects.create(date=timezone.now().date(), classroom=self.classroom)
        session = UserSession.objects.create(user=self.user, lesson_session=lesson)
        Goal.objects.create(user_session=session, raw_text="test")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["can_use_ai"])
        self.assertIn("Reflexion starten", response.content.decode())


class DashboardReflectionLinkTests(TestCase):
    def setUp(self):
        self.classroom = Classroom.objects.create(name="10A", use_ai=True)
        self.user = User.objects.create_user(
            pseudonym="kg1", gruppe=User.KG, classroom=self.classroom
        )
        self.client.force_login(self.user)

    def _create_goal(self):
        lesson = LessonSession.objects.create(date=timezone.now().date(), classroom=self.classroom)
        session = UserSession.objects.create(user=self.user, lesson_session=lesson)
        Goal.objects.create(user_session=session, raw_text="test")

    def test_link_hidden_without_goal(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Reflexion starten", response.content.decode())

    def test_link_visible_with_goal(self):
        self._create_goal()
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Reflexion starten", response.content.decode())


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


class DashboardProgressTests(TestCase):
    def setUp(self):
        self.classroom = Classroom.objects.create(name="10A")
        self.user = User.objects.create_user(pseudonym="u1", classroom=self.classroom)
        self.client.force_login(self.user)

    def test_progress_context_and_rendering(self):
        lesson = LessonSession.objects.create(date="2024-01-01", classroom=self.classroom)
        session = UserSession.objects.create(user=self.user, lesson_session=lesson)
        past_goal = Goal.objects.create(user_session=session, raw_text="alt")
        Goal.objects.filter(id=past_goal.id).update(created_at=timezone.now() - timedelta(days=1))
        OverallGoal.objects.create(user=self.user, text="Langfristig")
        goal1 = Goal.objects.create(user_session=session, raw_text="neu1")
        Reflection.objects.create(user_session=session, goal=goal1, result="yes", obstacles="", next_step="")
        Goal.objects.create(user_session=session, raw_text="neu2")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.context["completed_goals"], 1)
        self.assertEqual(response.context["open_goals"], 1)
        self.assertEqual(response.context["completion_rate"], 50)
        self.assertContains(response, "progressChart")
