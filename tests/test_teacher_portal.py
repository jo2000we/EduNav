from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.models import User
from lessons.models import Classroom
from teacher_portal.forms import ClassroomForm, SiteSettingsForm
from config.models import SiteSettings


class TeacherPortalTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("teacher", password="pw", is_staff=True)
        self.client.force_login(self.staff)

    def test_portal_view(self):
        url = reverse("teacher_portal:portal")
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert b"Site Settings" in resp.content
        assert b"Datenexport" in resp.content
        assert b"Auswertung" in resp.content

    def test_bulk_add_students_textarea(self):
        classroom = Classroom.objects.create(name="Class 1")
        url = reverse("teacher_portal:classroom_students", args=[classroom.pk])
        data = {"pseudonyms": "alpha\nbeta", "gruppe": User.VG}
        resp = self.client.post(url, data)
        assert resp.status_code == 302
        students = User.objects.filter(classroom=classroom)
        assert students.count() == 2
        assert {s.pseudonym for s in students} == {"alpha", "beta"}
        assert all(s.gruppe == User.VG for s in students)

    def test_bulk_add_students_csv(self):
        classroom = Classroom.objects.create(name="Class 1")
        url = reverse("teacher_portal:classroom_students", args=[classroom.pk])
        csv_content = "gamma\ndelta"
        uploaded = SimpleUploadedFile(
            "students.csv", csv_content.encode("utf-8"), content_type="text/csv"
        )
        resp = self.client.post(url, {"gruppe": User.KG, "csv_file": uploaded})
        assert resp.status_code == 302
        students = User.objects.filter(classroom=classroom)
        assert students.count() == 2
        assert {s.pseudonym for s in students} == {"gamma", "delta"}
        assert all(s.gruppe == User.KG for s in students)

    def test_portal_requires_staff(self):
        self.client.logout()
        student = User.objects.create_user("student", password="pw", is_staff=False)
        self.client.force_login(student)
        url = reverse("teacher_portal:portal")
        resp = self.client.get(url)
        assert resp.status_code == 302

    def test_template_renders_without_openai_attrs(self):
        rf = RequestFactory()
        request = rf.get("/")
        context = {
            "settings_form": SiteSettingsForm(instance=SiteSettings.get()),
            "classroom_form": ClassroomForm(),
            "classrooms": [],
        }
        render_to_string("teacher_portal/portal.html", context=context, request=request)
