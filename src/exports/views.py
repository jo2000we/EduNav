from __future__ import annotations

import csv
from io import StringIO, BytesIO
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View

from goals.models import Goal, KIInteraction
from reflections.models import Reflection, Note


def build_dataset():
    rows = []
    for goal in Goal.objects.select_related("user_session__user", "user_session__lesson_session"):
        user = goal.user_session.user
        lesson = goal.user_session.lesson_session
        reflection = Reflection.objects.filter(goal=goal).first()
        notes_count = Note.objects.filter(user_session=goal.user_session).count()
        ki_turns = KIInteraction.objects.filter(goal=goal).count()
        smart = goal.smart_score or {}
        rows.append({
            "user_id": user.id,
            "pseudonym": user.pseudonym,
            "klassengruppe": user.klassengruppe,
            "gruppe": user.gruppe,
            "lesson_date": lesson.date,
            "lesson_topic": lesson.topic,
            "goal_raw": goal.raw_text,
            "goal_final": goal.final_text,
            "smart_specific": smart.get("specific"),
            "smart_measurable": smart.get("measurable"),
            "smart_achievable": smart.get("achievable"),
            "smart_relevant": smart.get("relevant"),
            "smart_time_bound": smart.get("time_bound"),
            "smart_score": smart.get("score"),
            "ref_result": getattr(reflection, "result", None),
            "ref_obstacles": getattr(reflection, "obstacles", None),
            "ref_next_step": getattr(reflection, "next_step", None),
            "ref_next_step_source": getattr(reflection, "next_step_source", None),
            "notes_count": notes_count,
            "ki_turns": ki_turns,
        })
    return rows


@method_decorator(staff_member_required, name="dispatch")
class ExportCSVView(View):
    def get(self, request):
        rows = build_dataset()
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys() if rows else [])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        resp = HttpResponse(output.getvalue(), content_type="text/csv")
        resp['Content-Disposition'] = 'attachment; filename="export.csv"'
        return resp


try:
    import openpyxl
except Exception:  # pragma: no cover - dependency optional
    openpyxl = None

@method_decorator(staff_member_required, name="dispatch")
class ExportXLSXView(View):
    def get(self, request):
        rows = build_dataset()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(list(rows[0].keys()) if rows else [])
        for row in rows:
            ws.append(list(row.values()))
        output = BytesIO()
        wb.save(output)
        resp = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        resp['Content-Disposition'] = 'attachment; filename="export.xlsx"'
        return resp
