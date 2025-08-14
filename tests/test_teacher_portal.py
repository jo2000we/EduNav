from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class TeacherPortalTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("teacher", password="pw", is_staff=True)
        self.client.force_login(self.staff)

    def test_portal_view(self):
        url = reverse("teacher_portal:portal")
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert b"Site Settings" in resp.content
