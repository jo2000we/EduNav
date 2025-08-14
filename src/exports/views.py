from __future__ import annotations

import csv
import json
import uuid
from datetime import datetime
from io import StringIO, BytesIO
from django.http import HttpResponse, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count

from goals.models import Goal, KIInteraction, OverallGoal
from reflections.models import Reflection


def build_dataset(from_date=None, to_date=None, klass=None, group=None):
    qs = Goal.objects.select_related("user_session__user", "user_session__lesson_session")
    if from_date:
        qs = qs.filter(user_session__lesson_session__date__gte=from_date)
    if to_date:
        qs = qs.filter(user_session__lesson_session__date__lte=to_date)
    if klass:
        qs = qs.filter(user_session__user__classroom__name=klass)
    if group:
        qs = qs.filter(user_session__user__gruppe=group)
    goals = list(qs)
    # prefetch latest overall goals per user
    user_ids = {g.user_session.user_id for g in goals}
    overall_goals = (
        OverallGoal.objects.filter(user_id__in=user_ids)
        .order_by("user_id", "-created_at")
        .values("user_id", "text")
    )
    overall_map = {}
    for og in overall_goals:
        # keep first occurrence per user (newest due to ordering)
        overall_map.setdefault(og["user_id"], og["text"])

    rows = []
    for goal in goals:
        user = goal.user_session.user
        lesson = goal.user_session.lesson_session
        reflection = Reflection.objects.filter(goal=goal).first()
        ki_turns = KIInteraction.objects.filter(goal=goal).count()
        smart = goal.smart_score or {}
        rows.append(
            {
                "user_id": user.id,
                "pseudonym": user.pseudonym,
                "klassengruppe": getattr(user.classroom, "name", None),
                "gruppe": user.gruppe,
                "lesson_date": lesson.date,
                "lesson_topic": lesson.topic,
                "goal_raw": goal.raw_text,
                "goal_final": goal.final_text,
                "overall_goal": overall_map.get(user.id),
                "smart_specific": smart.get("specific"),
                "smart_measurable": smart.get("measurable"),
                "smart_achievable": smart.get("achievable"),
                "smart_relevant": smart.get("relevant"),
                "smart_time_bound": smart.get("time_bound"),
                "smart_score": smart.get("overall", smart.get("score")),
                "ref_result": getattr(reflection, "result", None),
                "ref_obstacles": getattr(reflection, "obstacles", None),
                "ref_next_step": getattr(reflection, "next_step", None),
                "ref_next_step_source": getattr(reflection, "next_step_source", None),
                "ki_turns": ki_turns,
            }
        )
    return rows, goals


@method_decorator(staff_member_required, name="dispatch")
class DashboardDataView(View):
    """Provide JSON stats for the admin dashboard charts."""

    def get(self, request):
        goals = Goal.objects.select_related("user_session__user")
        group_counts = (
            goals.values("user_session__user__gruppe")
            .annotate(count=Count("id"))
            .order_by()
        )
        labels = [gc["user_session__user__gruppe"] or "?" for gc in group_counts]
        data = [gc["count"] for gc in group_counts]
        ki_with = (
            KIInteraction.objects.filter(goal_id__in=goals.values_list("id", flat=True))
            .values("goal_id")
            .distinct()
            .count()
        )
        ki_total = goals.count()
        return JsonResponse(
            {
                "group_labels": labels,
                "group_data": data,
                "ki_labels": ["with_ki", "without_ki"],
                "ki_data": [ki_with, ki_total - ki_with],
            }
        )

@method_decorator(staff_member_required, name="dispatch")
class ExportCSVView(View):
    def get(self, request):
        from_date = parse_date(request.GET.get("from")) if request.GET.get("from") else None
        to_date = parse_date(request.GET.get("to")) if request.GET.get("to") else None
        klass = request.GET.get("class")
        group = request.GET.get("group")
        rows, _ = build_dataset(from_date, to_date, klass, group)
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
        from_date = parse_date(request.GET.get("from")) if request.GET.get("from") else None
        to_date = parse_date(request.GET.get("to")) if request.GET.get("to") else None
        klass = request.GET.get("class")
        group = request.GET.get("group")
        rows, goals = build_dataset(from_date, to_date, klass, group)
        exported_at = timezone.now().isoformat()
        for row in rows:
            row["exported_at"] = exported_at

        User = get_user_model()
        user_ids = {g.user_session.user_id for g in goals}
        users = User.objects.filter(id__in=user_ids)
        user_rows = [
            {
                "id": u.id,
                "pseudonym": u.pseudonym,
                "klassengruppe": getattr(u.classroom, "name", None),
                "gruppe": u.gruppe,
                "created_at": u.created_at,
                "exported_at": exported_at,
            }
        for u in users
        ]

        goal_rows = [
            {
                "id": g.id,
                "user_session": g.user_session_id,
                "raw_text": g.raw_text,
                "final_text": g.final_text,
                "smart_score": json.dumps(g.smart_score) if g.smart_score is not None else None,
                "created_at": g.created_at,
                "finalized_at": g.finalized_at,
                "exported_at": exported_at,
            }
            for g in goals
        ]

        goal_ids = [g.id for g in goals]
        overall_goal_rows = [
            {
                "id": og.id,
                "user": og.user_id,
                "text": og.text,
                "created_at": og.created_at,
                "exported_at": exported_at,
            }
            for og in OverallGoal.objects.filter(user_id__in=user_ids)
        ]

        reflection_rows = [
            {
                "id": r.id,
                "user_session": r.user_session_id,
                "goal": r.goal_id,
                "result": r.result,
                "obstacles": r.obstacles,
                "next_step": r.next_step,
                "next_step_source": r.next_step_source,
                "created_at": r.created_at,
                "exported_at": exported_at,
            }
            for r in Reflection.objects.filter(goal_id__in=goal_ids)
        ]

        ki_rows = [
            {
                "id": k.id,
                "goal": k.goal_id,
                "turn": k.turn,
                "role": k.role,
                "content": k.content,
                "created_at": k.created_at,
                "exported_at": exported_at,
            }
            for k in KIInteraction.objects.filter(goal_id__in=goal_ids)
        ]


        wb = openpyxl.Workbook()
        wb.remove(wb.active)

        def write_sheet(name, data):
            ws = wb.create_sheet(title=name)
            if data:
                ws.append(list(data[0].keys()))
                for row in data:
                    ws.append([
                        v.isoformat() if isinstance(v, datetime)
                        else str(v) if isinstance(v, uuid.UUID)
                        else v
                        for v in row.values()
                    ])

        write_sheet("Users", user_rows)
        write_sheet("Goals", goal_rows)
        write_sheet("OverallGoals", overall_goal_rows)
        write_sheet("Reflections", reflection_rows)
        write_sheet("KIInteractions", ki_rows)
        write_sheet("flat_dataset", rows)

        output = BytesIO()
        wb.save(output)
        resp = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp['Content-Disposition'] = 'attachment; filename="export.xlsx"'
        return resp
