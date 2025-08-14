from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError

from accounts.models import User
from lessons.models import Classroom, LessonSession, UserSession
from goals.models import Goal
from reflections.models import Reflection


class ReflectionAiToggleTests(TestCase):
    def setUp(self):
        self.classroom = Classroom.objects.create(name="10A", use_ai=True)
        self.user = User.objects.create_user(pseudonym="kg", gruppe=User.KG, classroom=self.classroom)
        self.client.force_login(self.user)
        lesson = LessonSession.objects.create(date=timezone.now().date(), classroom=self.classroom)
        session = UserSession.objects.create(user=self.user, lesson_session=lesson)
        Goal.objects.create(user_session=session, raw_text="test")

    def test_kg_user_does_not_see_ai_button(self):
        response = self.client.get(reverse("reflection"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["can_use_ai"])
        self.assertNotIn("KI-Vorschläge anzeigen", response.content.decode())


class ReflectionEdgeCaseTests(TestCase):
    def setUp(self):
        self.classroom = Classroom.objects.create(name="10A")
        self.user = User.objects.create_user(pseudonym="u1", classroom=self.classroom)
        self.client.force_login(self.user)

    def test_redirect_without_goal(self):
        response = self.client.get(reverse("reflection"))
        self.assertRedirects(response, reverse("dashboard"))

    def test_validation_error(self):
        lesson = LessonSession.objects.create(date=timezone.now().date(), classroom=self.classroom)
        session = UserSession.objects.create(user=self.user, lesson_session=lesson)
        goal = Goal.objects.create(user_session=session, raw_text="test")
        resp = self.client.post(
            "/api/reflections/",
            {"user_session": str(session.id), "goal": str(goal.id)},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("result", resp.json())


class ReflectionUniquenessTests(TestCase):
    def setUp(self):
        self.classroom = Classroom.objects.create(name="10A")
        self.user = User.objects.create_user(pseudonym="u1", classroom=self.classroom)
        lesson = LessonSession.objects.create(date=timezone.now().date(), classroom=self.classroom)
        self.session = UserSession.objects.create(user=self.user, lesson_session=lesson)
        self.goal = Goal.objects.create(user_session=self.session, raw_text="test")

    def test_duplicate_reflection_not_allowed(self):
        Reflection.objects.create(
            user_session=self.session,
            goal=self.goal,
            result="yes",
            obstacles="keine",
            next_step="weiter",
        )
        with self.assertRaises(IntegrityError):
            Reflection.objects.create(
                user_session=self.session,
                goal=self.goal,
                result="no",
                obstacles="keine",
                next_step="weiter",
            )
