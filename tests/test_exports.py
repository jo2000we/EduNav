from io import BytesIO

from django.test import TestCase
from django.contrib.auth import get_user_model

from lessons.models import LessonSession, UserSession
from goals.models import Goal, KIInteraction
from reflections.models import Reflection, Note
import openpyxl


class ExportViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client.force_login(User.objects.create_user(pseudonym="staff", password="pw", is_staff=True))
        self.lesson1 = LessonSession.objects.create(date="2024-01-01")
        self.lesson2 = LessonSession.objects.create(date="2024-05-01")
        self.user1 = User.objects.create_user(pseudonym="u1", gruppe=User.VG, klassengruppe="10A")
        self.user2 = User.objects.create_user(pseudonym="u2", gruppe=User.KG, klassengruppe="10B")
        self.session1 = UserSession.objects.create(user=self.user1, lesson_session=self.lesson1)
        self.session2 = UserSession.objects.create(user=self.user1, lesson_session=self.lesson2)
        self.session3 = UserSession.objects.create(user=self.user2, lesson_session=self.lesson1)
        self.goal1 = Goal.objects.create(user_session=self.session1, raw_text="g1")
        self.goal2 = Goal.objects.create(user_session=self.session2, raw_text="g2")
        self.goal3 = Goal.objects.create(user_session=self.session3, raw_text="g3")
        Reflection.objects.create(user_session=self.session2, goal=self.goal2, result="yes", obstacles="none", next_step="next", next_step_source="user")
        Note.objects.create(user_session=self.session2, content="note")
        KIInteraction.objects.create(goal=self.goal2, turn=1, role="user", content="hi")

    def test_csv_filters(self):
        resp = self.client.get("/api/export/csv/", {"from": "2024-02-01", "class": "10A", "group": "VG"})
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn("g2", content)
        self.assertNotIn("g1", content)
        self.assertNotIn("g3", content)

    def test_xlsx_contains_sheets_and_exported_at(self):
        resp = self.client.get("/api/export/xlsx/")
        self.assertEqual(resp.status_code, 200)
        wb = openpyxl.load_workbook(BytesIO(resp.content))
        self.assertEqual(set(wb.sheetnames), {"Users", "Goals", "Reflections", "KIInteractions", "Notes", "flat_dataset"})
        ws = wb["flat_dataset"]
        headers = [cell.value for cell in next(ws.iter_rows(max_row=1))]
        self.assertIn("exported_at", headers)
