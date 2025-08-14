from django.test import TestCase
from django.contrib.auth import get_user_model

from lessons.models import LessonSession, UserSession, Classroom
from goals.models import Goal, KIInteraction


class AdminDashboardTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(
            pseudonym="staff", password="pw", is_staff=True, gruppe=User.KG
        )
        self.user = User.objects.create_user(
            pseudonym="u1", password="pw", is_staff=False, gruppe=User.VG
        )
        classroom = Classroom.objects.create(name="10A")
        lesson = LessonSession.objects.create(date="2024-01-01", classroom=classroom)
        staff_session = UserSession.objects.create(user=self.staff, lesson_session=lesson)
        user_session = UserSession.objects.create(user=self.user, lesson_session=lesson)
        Goal.objects.create(user_session=staff_session, raw_text="g1")
        goal_with_ki = Goal.objects.create(user_session=user_session, raw_text="g2")
        KIInteraction.objects.create(goal=goal_with_ki, turn=1, role="user", content="hi")
        self.client.force_login(self.staff)

    def test_dashboard_requires_staff(self):
        resp = self.client.get("/admin/exports/dashboard/")
        self.assertEqual(resp.status_code, 200)
        self.client.logout()
        self.client.force_login(self.user)
        resp = self.client.get("/admin/exports/dashboard/")
        self.assertEqual(resp.status_code, 302)

    def test_data_endpoint_structure_and_access(self):
        resp = self.client.get("/api/export/dashboard-data/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for key in ["group_labels", "group_data", "ki_labels", "ki_data"]:
            self.assertIn(key, data)
        self.client.logout()
        self.client.force_login(self.user)
        resp = self.client.get("/api/export/dashboard-data/")
        self.assertEqual(resp.status_code, 302)
