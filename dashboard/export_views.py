import csv
import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from openpyxl import Workbook

from .models import Classroom, Student


def _minutes(hhmm):
    try:
        h, m = map(int, (hhmm or "0:0").split(":"))
        return h * 60 + m
    except Exception:
        return 0


def _time_delta(entry):
    p = {i.get("goal"): _minutes(i.get("time", "0:0")) for i in entry.time_planning or []}
    a = {i.get("goal"): _minutes(i.get("time", "0:0")) for i in entry.time_usage or []}
    keys = set(p) | set(a)
    return [
        {
            "Ziel": k,
            "Plan": p.get(k, 0),
            "Ist": a.get(k, 0),
            "Delta": a.get(k, 0) - p.get(k, 0),
        }
        for k in keys
    ]


@login_required
def export_classroom_data(request, classroom_id):
    """Placeholder view for exporting classroom data."""
    return HttpResponse("Export interface not implemented yet.")


def _entry_nested(entry):
    def _tp(lst):
        return [{"Ziel": item.get("goal"), "Zeit": item.get("time")} for item in lst]

    def _exp(lst):
        return [
            {"Ziel": item.get("goal"), "Indikator": item.get("indicator")} for item in lst
        ]

    def _tu(lst):
        return [{"Ziel": item.get("goal"), "Zeit": item.get("time")} for item in lst]

    def _sc(lst):
        return [
            {
                "Strategie": item.get("strategy"),
                "Genutzt": item.get("used"),
                "Sinnvoll": item.get("useful"),
                "Anpassung": item.get("change") or item.get("adaptation"),
            }
            for item in lst
        ]

    def _ga(lst):
        return [
            {
                "Ziel": item.get("goal"),
                "Ergebnis": item.get("achievement"),
                "Kommentar": item.get("comment"),
            }
            for item in lst
        ]

    return {
        "Datum": str(entry.session_date),
        "Planung": {
            "Ziele": entry.goals,
            "Prioritäten": entry.priorities,
            "Strategien": entry.strategies,
            "Ressourcen": entry.resources,
            "Zeitplanung": _tp(entry.time_planning),
            "Erwartungen": _exp(entry.expectations),
        },
        "Durchführung": {
            "Schritte": entry.steps,
            "Zeitnutzung": _tu(entry.time_usage),
            "Strategie-Check": _sc(entry.strategy_check),
            "Probleme": entry.problems,
            "Emotionen": entry.emotions,
        },
        "Reflexion": {
            "Zielerreichung": _ga(entry.goal_achievement),
            "Strategie-Bewertung": entry.strategy_evaluation,
            "Gelerntes (Inhaltlich)": entry.learned_subject,
            "Gelerntes (Arbeitsweise)": entry.learned_work,
            "War die Planung realistisch?": entry.planning_realistic,
            "Abweichungen von der Planung": entry.planning_deviations,
            "Motivation (Bewertung)": entry.motivation_rating,
            "Motivation verbessern": entry.motivation_improve,
            "Nächste Lernphase": entry.next_phase,
            "Strategie-Ausblick": entry.strategy_outlook,
            "Zeit-Delta": _time_delta(entry),
        },
    }


def _entry_flat(entry):
    def _join(lst):
        return "; ".join(lst) if lst else ""

    def _tp(lst):
        return "; ".join(
            f"{item.get('goal')} ({item.get('time')})" for item in lst
        )

    def _exp(lst):
        return "; ".join(
            f"{item.get('goal')}{': ' + item.get('indicator') if item.get('indicator') else ''}"
            for item in lst
        )

    def _sc(lst):
        parts = []
        for item in lst:
            txt = item.get("strategy", "")
            if item.get("used") is not None:
                txt += f" – {'genutzt' if item['used'] else 'nicht genutzt'}"
            if item.get("useful") is not None:
                txt += f", {'sinnvoll' if item['useful'] else 'nicht sinnvoll'}"
            ch = item.get("change") or item.get("adaptation")
            if ch:
                txt += f" – {ch}"
            parts.append(txt)
        return "; ".join(parts)

    def _ga(lst):
        return "; ".join(
            f"{item.get('goal')}: {item.get('achievement')}{' – ' + item.get('comment') if item.get('comment') else ''}"
            for item in lst
        )

    def _se(lst):
        parts = []
        for item in lst:
            txt = item.get("strategy", "")
            hv = item.get("helpful")
            if hv is not None:
                txt += f": {hv}"
            comment = item.get("comment") or item.get("reason")
            if comment:
                txt += f" – {comment}"
            if "reuse" in item:
                txt += f" (erneut: {item['reuse']})"
            parts.append(txt)
        return "; ".join(parts)

    def _td(lst):
        return "; ".join(
            f"{d['Ziel']}: {d['Delta']} Min" for d in lst
        )

    return {
        "Datum": str(entry.session_date),
        "Ziele": _join(entry.goals),
        "Prioritäten": _join(entry.priorities),
        "Strategien": _join(entry.strategies),
        "Ressourcen": _join(entry.resources),
        "Zeitplanung": _tp(entry.time_planning),
        "Erwartungen": _exp(entry.expectations),
        "Schritte": _join(entry.steps),
        "Zeitnutzung": _tp(entry.time_usage),
        "Strategie-Check": _sc(entry.strategy_check),
        "Probleme": entry.problems,
        "Emotionen": entry.emotions,
        "Zielerreichung": _ga(entry.goal_achievement),
        "Strategie-Bewertung": _se(entry.strategy_evaluation),
        "Gelerntes (Inhaltlich)": entry.learned_subject,
        "Gelerntes (Arbeitsweise)": entry.learned_work,
        "War die Planung realistisch?": entry.planning_realistic,
        "Abweichungen von der Planung": entry.planning_deviations,
        "Motivation (Bewertung)": entry.motivation_rating,
        "Motivation verbessern": entry.motivation_improve,
        "Nächste Lernphase": entry.next_phase,
        "Strategie-Ausblick": entry.strategy_outlook,
        "Zeit-Delta": _td(_time_delta(entry)),
    }


@login_required
def export_student_data(request, classroom_id, student_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    student = get_object_or_404(Student, id=student_id, classroom=classroom)
    fmt = request.GET.get("format", "json").lower()
    group_label = (
        "Kontrollgruppe"
        if classroom.group_type == Classroom.GroupType.CONTROL
        else "Experimentalgruppe"
    )
    entries = student.entries.order_by("session_date")

    if fmt == "json":
        data = {
            "Pseudonym": student.pseudonym,
            "Gruppenzugehörigkeit": group_label,
            "Gesamtziel": student.overall_goal,
            "Fälligkeitsdatum des Gesamtziels": student.overall_goal_due_date.isoformat()
            if student.overall_goal_due_date
            else None,
            "Einträge": [_entry_nested(e) for e in entries],
        }
        response = HttpResponse(
            json.dumps(data, ensure_ascii=False, indent=2),
            content_type="application/json",
        )
        response["Content-Disposition"] = (
            f"attachment; filename={slugify(student.pseudonym)}.json"
        )
        return response

    fieldnames = [
        "Pseudonym",
        "Gruppenzugehörigkeit",
        "Gesamtziel",
        "Fälligkeitsdatum des Gesamtziels",
        "Datum",
        "Ziele",
        "Prioritäten",
        "Strategien",
        "Ressourcen",
        "Zeitplanung",
        "Erwartungen",
        "Schritte",
        "Zeitnutzung",
        "Strategie-Check",
        "Probleme",
        "Emotionen",
        "Zielerreichung",
        "Strategie-Bewertung",
        "Gelerntes (Inhaltlich)",
        "Gelerntes (Arbeitsweise)",
        "War die Planung realistisch?",
        "Abweichungen von der Planung",
        "Motivation (Bewertung)",
        "Motivation verbessern",
        "Nächste Lernphase",
        "Strategie-Ausblick",
        "Zeit-Delta",
    ]

    rows = []
    for e in entries:
        row = {
            "Pseudonym": student.pseudonym,
            "Gruppenzugehörigkeit": group_label,
            "Gesamtziel": student.overall_goal or "",
            "Fälligkeitsdatum des Gesamtziels": student.overall_goal_due_date or "",
        }
        row.update(_entry_flat(e))
        rows.append(row)

    if fmt == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f"attachment; filename={slugify(student.pseudonym)}.csv"
        )
        writer = csv.DictWriter(response, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        return response

    if fmt == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.append(fieldnames)
        for row in rows:
            ws.append([row.get(fn, "") for fn in fieldnames])
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = (
            f"attachment; filename={slugify(student.pseudonym)}.xlsx"
        )
        wb.save(response)
        return response

    return HttpResponse(status=400)

