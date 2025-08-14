from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from lessons.models import Classroom


class ReflectionAiToggleTests(TestCase):
    def setUp(self):
        self.classroom = Classroom.objects.create(name="10A", use_ai=True)
        self.user = User.objects.create_user(pseudonym="kg", gruppe=User.KG, classroom=self.classroom)
        self.client.force_login(self.user)

    def test_kg_user_does_not_see_ai_button(self):
        response = self.client.get(reverse("reflection"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["can_use_ai"])
        self.assertNotIn("KI-Vorschläge anzeigen", response.content.decode())
