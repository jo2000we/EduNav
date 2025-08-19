from functools import wraps
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Student, SRLEntry, AppSettings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import json
from django.urls import reverse
from datetime import date
from .forms import (
    PseudoForm,
    PasswordLoginForm,
    SetPasswordForm,
    PlanningForm,
    ExecutionForm,
    ReflectionForm,
)
from .export_views import _entry_nested
from django.test import RequestFactory
import re
import time


def _total_minutes(items):
    total = 0
    for idx, item in enumerate(items):
        t = item.get("time")
        if not t:
            continue
        norm = _normalize_time(t)
        h, m = [int(x) for x in norm.split(":")]
        total += h * 60 + m
    return total


TIME_RE = re.compile(r"^\d{1,2}:\d{1,2}$")


def _normalize_time(t):
    if not isinstance(t, str) or not TIME_RE.match(t):
        raise ValueError("HH:MM erwartet")
    h, m = [int(x) for x in t.split(":")]
    if h < 0 or m < 0 or m > 59:
        raise ValueError("Ungültige Zeit")
    return f"{h:02d}:{m:02d}"


def _clean_list(lst):
    seen = set()
    out = []
    for s in lst or []:
        x = " ".join((s or "").split())
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _student_diary_json(student):
    entries = student.entries.order_by("session_date")
    return {
        "Pseudonym": student.pseudonym,
        "Gesamtziel": student.overall_goal,
        "Fälligkeitsdatum des Gesamtziels": student.overall_goal_due_date.isoformat()
        if student.overall_goal_due_date
        else None,
        "Einträge": [_entry_nested(e) for e in entries],
    }


def _openai_client():
    settings = AppSettings.load()
    if not settings.openai_api_key:
        return None, settings
    try:
        from openai import OpenAI
    except ModuleNotFoundError:
        return None, settings
    return OpenAI(api_key=settings.openai_api_key), settings


# System and developer prompts for each phase
PLAN_SYSTEM_PROMPT = (
    "Du bist ein SRL-Coach für die Planungsphase. Arbeite strikt phasengetreu "
    "nach anerkannten SRL-Modellen. Sprich kurz, freundlich, konkret. Eine "
    "Frage pro Nachricht. Keine Listen, kein Markdown. Maximal zwei Sätze (<240 Zeichen) pro Nachricht. "
    "Ziel: gültiges JSON für POST \"/dashboard/api/entry/new/\". "
    "Halte dich exakt an das geforderte Schema und an HH:MM. Prüfe Summen gegen "
    "Minutenlimit (Standard 90 Min, außer Limit im Kontext). Tool-Antworten "
    "enthalten 'status' und 'body'. Bei status != 200: lies error/errors im body, "
    "erkläre präzise, stelle Korrekturfragen, sende korrigiertes JSON erneut. "
    "Nach erfolgreichem Speichern sofort STOPP. Sende nur: 'Planung gespeichert. entry_id: <ID>'. Keine weiteren Inhalte, keine Ratschläge."
)

PLAN_DEVELOPER_PROMPT = (
    "Eingabe ist ein vollständiges SRL-Tagebuch als JSON (siehe Nutzer-Nachricht) "
    "+ aktuelles Datum.\n"
    "1. Lies Pseudonym, Gesamtziel, Fälligkeitsdatum, letzte 'Nächste Lernphase'.\n"
    "2. Rechne verbleibende Tage/Wochen.\n"
    "3. Führe die Schritte 1–9 des Planungs-Ablaufs aus.\n"
    "4. Baue nur bei Bestätigung das JSON exakt so: {\n"
    "  'goals': ['...'],\n"
    "  'priorities': [{'goal':'...','priority':true}],\n"
    "  'strategies': ['...'],\n"
    "  'resources': ['...'],\n"
    "  'time_planning': [{'goal':'...','time':'HH:MM'}],\n"
    "  'expectations': [{'goal':'...','indicator':'...'}]\n"
    "}.\n"
    "5. Sende es an /dashboard/api/entry/new/ und speichere entry_id für die nächste Phase.\n"
    "6. Wenn 400/Fehler: zeige fehlerhafte Felder, frage gezielt nach Korrektur, "
    "validiere erneut, re-POST.\n"
    "7. Verwende knappe Bullet-Prompts; maximal zwei Optionen pro Frage.\n"
    "Maximal ein Submit pro Sitzung.\n"
    "Keine Listen, kein Markdown. Maximal zwei Sätze (<240 Zeichen) pro Nachricht. Nach erfolgreichem Speichern sofort stoppen und nur 'Planung gespeichert. entry_id: <ID>' senden."
)

EXEC_SYSTEM_PROMPT = (
    "Du bist ein SRL-Coach für die Durchführungsphase. Dokumentiere Schritte, "
    "reale Zeiten, Strategie-Check, Probleme und Emotionen. Eine Frage pro "
    "Nachricht. Keine Listen, kein Markdown. Maximal zwei Sätze (<240 Zeichen) pro Nachricht. "
    "Halte dich exakt an das JSON-Schema der Durchführungsphase. "
    "Prüfe HH:MM und Summen. Tool-Antworten enthalten 'status' und 'body'. Bei "
    "status != 200: präzise Korrektur basierend auf error/errors. "
    "Nach erfolgreichem Speichern sofort STOPP. Sende nur: 'Durchführung gespeichert.'"
)

EXEC_DEVELOPER_PROMPT = (
    "Eingabe: SRL-Tagebuch-JSON inkl. entry_id der aktuellen Sitzung.\n"
    "1. Hole geplante Ziele/Strategien der laufenden entry_id.\n"
    "2. Führe die Schritte 1–7 im Ablauf aus.\n"
    "3. Baue JSON exakt: { 'steps': ['...'], 'time_usage': [{'goal':'...','time':'HH:MM'}],"
    " 'strategy_check': [{'strategy':'...','used':true,'useful':false,'change':'...'}],"
    " 'problems':'...', 'emotions':'...' }.\n"
    "4. POST an /dashboard/api/entry/<entry_id>/execution/.\n"
    "5. Fehlerhandling wie beschrieben.\n"
    "6. Stil: knappe Stichworte, lösungsorientiert.\n"
    "Maximal ein Submit pro Sitzung.\n"
    "Keine Listen, kein Markdown. Maximal zwei Sätze (<240 Zeichen) pro Nachricht. Nach erfolgreichem Speichern sofort stoppen und nur 'Durchführung gespeichert.' senden."
)

REFL_SYSTEM_PROMPT = (
    "Du bist ein SRL-Coach für die Reflexionsphase. Erfasse Zielerreichung, "
    "Strategiewirkung, Gelerntes, Realismus, Abweichungen, Motivation, nächste "
    "Phase und Strategie-Ausblick. Eine Frage pro Nachricht. Keine Listen, kein Markdown. "
    "Maximal zwei Sätze (<240 Zeichen) pro Nachricht. Halte dich exakt an das JSON-Schema der "
    "Reflexion. Knappe, präzise Sprache. Tool-Antworten enthalten 'status' und "
    "'body'. Bei status != 200: benenne Fehler präzise, korrigiere, re-POST. "
    "Nach erfolgreichem Speichern sofort STOPP. Sende nur: 'Reflexion gespeichert.'"
)

REFL_DEVELOPER_PROMPT = (
    "Eingabe: SRL-Tagebuch-JSON inkl. entry_id und zugehörigen Planungs-/Durchführungsdaten.\n"
    "1. Lade die heute geplanten Ziele (Reihenfolge = goal_achievement).\n"
    "2. Führe die Schritte 1–7 aus.\n"
    "3. Baue JSON exakt: { 'goal_achievement':[{'goal':'...','achievement':'vollständig','comment':'...'}],"
    " 'strategy_evaluation':[{'strategy':'...','helpful':'ja|teilweise|nein','comment':'...','reuse':'ja|nein|vielleicht'}],"
    " 'learned_subject':'...', 'learned_work':'...', 'planning_realistic':'...',"
    " 'planning_deviations':'...', 'motivation_rating':'7/10', 'motivation_improve':'...',"
    " 'next_phase':'...', 'strategy_outlook':'...' }.\n"
    "4. POST an /dashboard/api/entry/<entry_id>/reflection/.\n"
    "5. Fehlerhandling wie beschrieben.\n"
    "6. Vorschläge aus Planung/Durchführung dürfen gespiegelt werden.\n"
    "Maximal ein Submit pro Sitzung.\n"
    "Keine Listen, kein Markdown. Maximal zwei Sätze (<240 Zeichen) pro Nachricht. Nach erfolgreichem Speichern sofort stoppen und nur 'Reflexion gespeichert.' senden."
)


def _call_phase_api(phase, request, payload, entry_id=None):
    """Call internal JSON endpoints for a given phase."""
    rf = RequestFactory()
    body = json.dumps(payload)
    if phase == "planning":
        api_request = rf.post("/", body, content_type="application/json")
        api_request.session = request.session
        api_request.user = request.user
        return create_entry_json(api_request)
    if phase == "execution" and entry_id is not None:
        api_request = rf.post("/", body, content_type="application/json")
        api_request.session = request.session
        api_request.user = request.user
        return add_execution_json(api_request, entry_id)
    if phase == "reflection" and entry_id is not None:
        api_request = rf.post("/", body, content_type="application/json")
        api_request.session = request.session
        api_request.user = request.user
        return add_reflection_json(api_request, entry_id)
    return JsonResponse({"error": "Invalid phase"}, status=400)


def _chat_phase(request, phase, messages, entry_id=None):
    client, app_settings = _openai_client()
    if client is None:
        return {"error": "OpenAI API key not configured"}

    temperature = (
        app_settings.openai_temperature
        if app_settings.openai_temperature is not None
        else 0.2
    )

    model = None
    for candidate in [app_settings.openai_model, "gpt-4o-mini", "gpt-4o"]:
        if not candidate:
            continue
        try:
            client.models.retrieve(candidate)
            model = candidate
            break
        except Exception:
            continue
    if model is None:
        return {"error": "No valid OpenAI model configured"}

    student = Student.objects.get(id=request.session["student_id"])
    diary = _student_diary_json(student)
    minute_limit = student.classroom.max_planning_execution_minutes or 90

    if not messages:
        intro = (
            f"Hier ist das aktuelle SRL-Tagebuch (JSON). Bitte beginne mit der "
            f"{phase.capitalize()}sphase für die nächste Doppelstunde.\n"
            f"{json.dumps(diary, ensure_ascii=False)}\n"
            f"Aktuelles Datum: {date.today().isoformat()}\n"
            f"Klassen-Minutenlimit je Doppelstunde: {minute_limit}"
        )
        messages = [{"role": "user", "content": intro}]

    system_prompt = {
        "planning": PLAN_SYSTEM_PROMPT,
        "execution": EXEC_SYSTEM_PROMPT,
        "reflection": REFL_SYSTEM_PROMPT,
    }[phase]
    developer_prompt = {
        "planning": PLAN_DEVELOPER_PROMPT,
        "execution": EXEC_DEVELOPER_PROMPT,
        "reflection": REFL_DEVELOPER_PROMPT,
    }[phase]

    combined_prompt = f"{system_prompt}\n\n{developer_prompt}\n\nMinutenlimit: {minute_limit}"

    full_messages = [{"role": "system", "content": combined_prompt}] + messages

    tools = []
    if phase == "planning":
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "submit_planning",
                    "description": "Speichert die Planungsdaten und gibt entry_id zurück",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "goals": {"type": "array", "items": {"type": "string"}},
                            "priorities": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "goal": {"type": "string"},
                                        "priority": {"type": "boolean"},
                                    },
                                    "required": ["goal", "priority"],
                                },
                            },
                            "strategies": {"type": "array", "items": {"type": "string"}},
                            "resources": {"type": "array", "items": {"type": "string"}},
                            "time_planning": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "goal": {"type": "string"},
                                        "time": {"type": "string"},
                                    },
                                    "required": ["goal", "time"],
                                },
                            },
                            "expectations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "goal": {"type": "string"},
                                        "indicator": {"type": "string"},
                                    },
                                    "required": ["goal", "indicator"],
                                },
                            },
                        },
                        "required": [
                            "goals",
                            "priorities",
                            "strategies",
                            "resources",
                            "time_planning",
                            "expectations",
                        ],
                    },
                },
            }
        ]
    elif phase == "execution":
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "submit_execution",
                    "description": "Speichert die Durchführungsdaten",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "steps": {"type": "array", "items": {"type": "string"}},
                            "time_usage": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "goal": {"type": "string"},
                                        "time": {"type": "string"},
                                    },
                                    "required": ["goal", "time"],
                                },
                            },
                            "strategy_check": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "strategy": {"type": "string"},
                                        "used": {"type": "boolean"},
                                        "useful": {"type": "boolean"},
                                        "change": {"type": "string"},
                                    },
                                    "required": ["strategy", "used", "useful"],
                                },
                            },
                            "problems": {"type": "string"},
                            "emotions": {"type": "string"},
                        },
                        "required": [
                            "steps",
                            "time_usage",
                            "strategy_check",
                            "problems",
                            "emotions",
                        ],
                    },
                },
            }
        ]
    else:  # reflection
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "submit_reflection",
                    "description": "Speichert die Reflexionsdaten",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "goal_achievement": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "goal": {"type": "string"},
                                        "achievement": {"type": "string"},
                                        "comment": {"type": "string"},
                                    },
                                    "required": ["goal", "achievement", "comment"],
                                },
                            },
                            "strategy_evaluation": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "strategy": {"type": "string"},
                                        "helpful": {
                                            "type": "string",
                                            "enum": ["ja", "teilweise", "nein"],
                                        },
                                        "comment": {"type": "string"},
                                        "reuse": {
                                            "type": "string",
                                            "enum": ["ja", "nein", "vielleicht"],
                                        },
                                    },
                                    "required": ["strategy", "helpful", "comment", "reuse"],
                                },
                            },
                            "learned_subject": {"type": "string"},
                            "learned_work": {"type": "string"},
                            "planning_realistic": {"type": "string"},
                            "planning_deviations": {"type": "string"},
                            "motivation_rating": {"type": "string"},
                            "motivation_improve": {"type": "string"},
                            "next_phase": {"type": "string"},
                            "strategy_outlook": {"type": "string"},
                        },
                        "required": [
                            "goal_achievement",
                            "strategy_evaluation",
                            "learned_subject",
                            "learned_work",
                            "planning_realistic",
                            "planning_deviations",
                            "motivation_rating",
                            "motivation_improve",
                            "next_phase",
                            "strategy_outlook",
                        ],
                    },
                },
            }
        ]

    submitted = False
    current_entry_id = entry_id
    for _ in range(8):
        for attempt in range(2):
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=full_messages,
                    tools=tools,
                    temperature=temperature,
                    max_tokens=200,
                )
                break
            except Exception as e:
                err_text = str(e)
                if "RateLimit" in e.__class__.__name__ or "rate limit" in err_text.lower():
                    if attempt == 0:
                        time.sleep(1)
                        continue
                    return {"error": "Gerade ausgelastet. Bitte in ein paar Sekunden erneut senden."}
                return {"error": f"OpenAI error: {e.__class__.__name__}"}
        else:
            return {"error": "Gerade ausgelastet. Bitte in ein paar Sekunden erneut senden."}
        message = completion.choices[0].message
        finish = completion.choices[0].finish_reason
        if finish == "tool_calls" and message.tool_calls:
            for call in message.tool_calls:
                if submitted:
                    msg = (
                        f"Plan gespeichert – Eintrags-ID {current_entry_id}"
                        if phase == "planning"
                        else f"{phase.capitalize()} bereits gespeichert"
                    )
                    full_messages.append({"role": "assistant", "content": msg})
                    return {"reply": msg, "entry_id": current_entry_id}
                full_messages.append({"role": message.role, "tool_calls": [call]})
                args = json.loads(call.function.arguments or "{}")
                api_resp = _call_phase_api(phase, request, args, current_entry_id)
                status = getattr(api_resp, "status_code", 0)
                if phase == "planning" and status == 200:
                    try:
                        current_entry_id = json.loads(api_resp.content).get("entry_id")
                    except Exception:
                        pass
                if status == 200:
                    submitted = True
                    msg = (
                        f"Planung gespeichert. entry_id: {current_entry_id}"
                        if phase == "planning"
                        else f"{phase.capitalize()} gespeichert."
                    )
                    return {"reply": msg, "entry_id": current_entry_id}
                tool_payload = {
                    "status": status,
                    "body": api_resp.content.decode(errors="replace"),
                    "content_type": getattr(api_resp, "headers", {}).get("Content-Type", ""),
                }
                full_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": call.function.name,
                        "content": json.dumps(tool_payload, ensure_ascii=False),
                    }
                )
            continue
        if message.content:
            full_messages.append({"role": message.role, "content": message.content})
        return {"reply": message.content or "", "entry_id": current_entry_id}
    return {"error": "Conversation loop limit reached"}


def student_login(request):
    form = PseudoForm()
    return render(request, "dashboard/student_login.html", {"form": form})


def student_login_step(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    if "password1" in request.POST:
        form = SetPasswordForm(request.POST)
        pseudonym = request.POST.get("pseudonym", "")
        if form.is_valid():
            student = get_object_or_404(Student, pseudonym=pseudonym)
            student.set_password(form.cleaned_data["password1"])
            request.session["student_id"] = student.id
            response = HttpResponse(status=204)
            response["HX-Redirect"] = reverse("student_dashboard")
            return response
        return render(
            request,
            "dashboard/partials/password_set_form.html",
            {"form": form, "pseudonym": pseudonym},
        )

    if "password" in request.POST:
        form = PasswordLoginForm(request.POST)
        pseudonym = request.POST.get("pseudonym", "")
        if form.is_valid():
            try:
                student = Student.objects.get(pseudonym=pseudonym)
                if student.check_password(form.cleaned_data["password"]):
                    request.session["student_id"] = student.id
                    response = HttpResponse(status=204)
                    response["HX-Redirect"] = reverse("student_dashboard")
                    return response
                form.add_error("password", "Falsches Passwort")
            except Student.DoesNotExist:
                form.add_error(None, "Unbekanntes Pseudonym")
        return render(
            request,
            "dashboard/partials/password_enter_form.html",
            {"form": form, "pseudonym": pseudonym},
        )

    form = PseudoForm(request.POST)
    if form.is_valid():
        pseudonym = form.cleaned_data["pseudonym"]
        try:
            student = Student.objects.get(pseudonym=pseudonym)
            if student.password:
                form_pass = PasswordLoginForm()
                return render(
                    request,
                    "dashboard/partials/password_enter_form.html",
                    {"form": form_pass, "pseudonym": pseudonym},
                )
            form_set = SetPasswordForm()
            return render(
                request,
                "dashboard/partials/password_set_form.html",
                {"form": form_set, "pseudonym": pseudonym},
            )
        except Student.DoesNotExist:
            return render(
                request,
                "dashboard/partials/pseudonym_error.html",
                {"error": "Unbekanntes Pseudonym"},
            )
    return render(
        request,
        "dashboard/partials/pseudonym_error.html",
        {"error": "Ungültige Eingabe"},
    )


def student_logout(request):
    request.session.pop("student_id", None)
    return redirect("student_login")


def student_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get("student_id"):
            return redirect("student_login")
        return view_func(request, *args, **kwargs)

    return _wrapped


@student_required
def student_dashboard(request):
    student = Student.objects.get(id=request.session["student_id"])
    entries = student.entries.order_by("-session_date")
    template = (
        "dashboard/control_student_dashboard.html"
        if student.classroom.group_type == student.classroom.GroupType.CONTROL
        else "dashboard/experimental_student_dashboard.html"
    )
    context = {
        "student": student,
        "entries": entries,
        "planning_form": PlanningForm(),
        "execution_form": ExecutionForm(),
        "reflection_form": ReflectionForm(),
        "can_create_entry": student.can_create_entry(),
    }
    return render(request, template, context)


@student_required
def create_entry(request):
    student = Student.objects.get(id=request.session["student_id"])
    if not student.can_create_entry():
        return redirect("student_dashboard")
    if request.method == "POST":
        form = PlanningForm(request.POST)
        if form.is_valid():
            planning_minutes = _total_minutes(
                form.cleaned_data.get("time_planning", [])
            )
            limit = student.classroom.max_planning_execution_minutes
            if limit and planning_minutes > limit:
                messages.error(
                    request,
                    f"Die Gesamtzeit darf {limit} Minuten nicht überschreiten.",
                )
            else:
                entry = form.save(commit=False)
                entry.student = student
                entry.save()
    return redirect("student_dashboard")


@student_required
def add_execution(request, entry_id):
    student = Student.objects.get(id=request.session["student_id"])
    entry = get_object_or_404(SRLEntry, id=entry_id, student=student)
    if request.method == "POST":
        form = ExecutionForm(request.POST, instance=entry)
        if form.is_valid():
            usage_minutes = _total_minutes(form.cleaned_data.get("time_usage", []))
            limit = student.classroom.max_planning_execution_minutes
            if limit and usage_minutes > limit:
                messages.error(
                    request,
                    f"Die Gesamtzeit darf {limit} Minuten nicht überschreiten.",
                )
            else:
                form.save()
    return redirect("student_dashboard")


@student_required
def add_reflection(request, entry_id):
    student = Student.objects.get(id=request.session["student_id"])
    entry = get_object_or_404(SRLEntry, id=entry_id, student=student)
    if request.method == "POST":
        form = ReflectionForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")
    return redirect("student_dashboard")


@student_required
@require_POST
def create_entry_json(request):
    """Create a new SRL entry using JSON data.

    Expected JSON format:
    {
      "goals": ["str", ...],
      "priorities": [{"goal": "str", "priority": bool}, ...],
      "strategies": ["str", ...],
      "resources": ["str", ...],
      "time_planning": [{"goal": "str", "time": "HH:MM"}, ...],
      "expectations": [{"goal": "str", "indicator": "str"}, ...]
    }
    """
    student = Student.objects.get(id=request.session["student_id"])
    if not student.can_create_entry():
        return JsonResponse({"error": "Entry limit reached"}, status=403)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    for key in ["goals", "strategies", "resources"]:
        payload[key] = _clean_list(payload.get(key, []))

    for item in payload.get("priorities", []):
        item["goal"] = " ".join((item.get("goal", "")).split())

    for item in payload.get("time_planning", []):
        item["goal"] = " ".join((item.get("goal", "")).split())

    for item in payload.get("expectations", []):
        item["goal"] = " ".join((item.get("goal", "")).split())
        item["indicator"] = " ".join((item.get("indicator", "")).split())

    normalized = []
    for idx, item in enumerate(payload.get("time_planning", [])):
        try:
            item["time"] = _normalize_time(item.get("time"))
        except ValueError as e:
            return JsonResponse({"error": f"time_planning[{idx}].time {e}"}, status=400)
        normalized.append(item)
    payload["time_planning"] = normalized

    form_data = {
        field: json.dumps(payload.get(field, []))
        for field in [
            "goals",
            "priorities",
            "strategies",
            "resources",
            "time_planning",
            "expectations",
        ]
    }
    form = PlanningForm(form_data)
    if form.is_valid():
        planning_minutes = _total_minutes(form.cleaned_data.get("time_planning", []))
        limit = student.classroom.max_planning_execution_minutes
        if limit and planning_minutes > limit:
            return JsonResponse(
                {"error": f"Die Gesamtzeit darf {limit} Minuten nicht überschreiten."},
                status=400,
            )
        entry = form.save(commit=False)
        entry.student = student
        entry.save()
        return JsonResponse({"entry_id": entry.id})
    return JsonResponse({"errors": form.errors}, status=400)


@student_required
@require_POST
def add_execution_json(request, entry_id):
    """Update execution phase for an entry using JSON data.

    Expected JSON format:
    {
      "steps": ["str", ...],
      "time_usage": [{"goal": "str", "time": "HH:MM"}, ...],
      "strategy_check": [{"strategy": "str", "used": bool, "useful": bool, "change": "str" (optional)}, ...],
      "problems": "str",
      "emotions": "str"
    }
    """
    student = Student.objects.get(id=request.session["student_id"])
    entry = get_object_or_404(SRLEntry, id=entry_id, student=student)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    payload["steps"] = _clean_list(payload.get("steps", []))
    normalized = []
    for idx, item in enumerate(payload.get("time_usage", [])):
        try:
            item["time"] = _normalize_time(item.get("time"))
        except ValueError as e:
            return JsonResponse({"error": f"time_usage[{idx}].time {e}"}, status=400)
        normalized.append(item)
    payload["time_usage"] = normalized
    cleaned_sc = []
    seen = set()
    for sc in payload.get("strategy_check", []):
        if "adaptation" in sc and "change" not in sc:
            sc["change"] = sc.pop("adaptation")
        sc["strategy"] = " ".join((sc.get("strategy", "").split()))
        if sc.get("change"):
            sc["change"] = " ".join(sc["change"].split())
        name = sc.get("strategy")
        if name and name not in seen:
            seen.add(name)
            cleaned_sc.append(sc)
    payload["strategy_check"] = cleaned_sc
    form_data = {
        "steps": json.dumps(payload.get("steps", [])),
        "time_usage": json.dumps(payload.get("time_usage", [])),
        "strategy_check": json.dumps(payload.get("strategy_check", [])),
        "problems": payload.get("problems", ""),
        "emotions": payload.get("emotions", ""),
    }
    form = ExecutionForm(form_data, instance=entry)
    if form.is_valid():
        usage_minutes = _total_minutes(form.cleaned_data.get("time_usage", []))
        limit = student.classroom.max_planning_execution_minutes
        if limit and usage_minutes > limit:
            return JsonResponse(
                {"error": f"Die Gesamtzeit darf {limit} Minuten nicht überschreiten."},
                status=400,
            )
        form.save()
        return JsonResponse({"status": "ok"})
    return JsonResponse({"errors": form.errors}, status=400)


@student_required
@require_POST
def add_reflection_json(request, entry_id):
    """Update reflection phase for an entry using JSON data.

    Expected JSON format:
    {
      "goal_achievement": [{"goal": "str", "achievement": "str", "comment": "str"}, ...],
      "strategy_evaluation": [{"strategy": "str", "helpful": "ja|teilweise|nein", "comment": "str", "reuse": "ja|nein|vielleicht"}, ...],
      "learned_subject": "str",
      "learned_work": "str",
      "planning_realistic": "str",
      "planning_deviations": "str",
      "motivation_rating": "str",
      "motivation_improve": "str",
      "next_phase": "str",
      "strategy_outlook": "str"
    }
    """
    student = Student.objects.get(id=request.session["student_id"])
    entry = get_object_or_404(SRLEntry, id=entry_id, student=student)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    for se in payload.get("strategy_evaluation", []):
        if isinstance(se.get("helpful"), bool):
            se["helpful"] = "ja" if se["helpful"] else "nein"
        if isinstance(se.get("reuse"), bool):
            se["reuse"] = "ja" if se["reuse"] else "nein"
        if "reason" in se and "comment" not in se:
            se["comment"] = se.pop("reason")
        se["strategy"] = " ".join((se.get("strategy", "").split()))
    ga_list = payload.get("goal_achievement", [])
    planned_goals = entry.goals or []
    if ga_list and planned_goals:
        for i, ga in enumerate(ga_list):
            if "goal" not in ga and i < len(planned_goals):
                ga["goal"] = planned_goals[i]
    form_data = {
        "goal_achievement": json.dumps(ga_list),
        "strategy_evaluation": json.dumps(payload.get("strategy_evaluation", [])),
        "learned_subject": payload.get("learned_subject", ""),
        "learned_work": payload.get("learned_work", ""),
        "planning_realistic": payload.get("planning_realistic", ""),
        "planning_deviations": payload.get("planning_deviations", ""),
        "motivation_rating": payload.get("motivation_rating", ""),
        "motivation_improve": payload.get("motivation_improve", ""),
        "next_phase": payload.get("next_phase", ""),
        "strategy_outlook": payload.get("strategy_outlook", ""),
    }
    form = ReflectionForm(form_data, instance=entry)
    if form.is_valid():
        form.save()
        return JsonResponse({"status": "ok"})
    return JsonResponse({"errors": form.errors}, status=400)


# Chatbot views
@student_required
@require_POST
def chat_planning(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    messages = payload.get("messages", [])
    result = _chat_phase(request, "planning", messages)
    if "error" in result:
        status = 502 if result["error"].startswith("OpenAI") else 400
        if result["error"] == "Conversation loop limit reached":
            status = 500
        return JsonResponse(result, status=status)
    resp = {"reply": result["reply"]}
    if result.get("entry_id") is not None:
        resp["entry_id"] = result["entry_id"]
    return JsonResponse(resp)


@student_required
@require_POST
def chat_execution(request, entry_id):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    messages = payload.get("messages", [])
    result = _chat_phase(request, "execution", messages, entry_id=entry_id)
    if "error" in result:
        status = 502 if result["error"].startswith("OpenAI") else 400
        if result["error"] == "Conversation loop limit reached":
            status = 500
        return JsonResponse(result, status=status)
    resp = {"reply": result["reply"]}
    if result.get("entry_id") is not None:
        resp["entry_id"] = result["entry_id"]
    return JsonResponse(resp)


@student_required
@require_POST
def chat_reflection(request, entry_id):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    messages = payload.get("messages", [])
    result = _chat_phase(request, "reflection", messages, entry_id=entry_id)
    if "error" in result:
        status = 502 if result["error"].startswith("OpenAI") else 400
        if result["error"] == "Conversation loop limit reached":
            status = 500
        return JsonResponse(result, status=status)
    resp = {"reply": result["reply"]}
    if result.get("entry_id") is not None:
        resp["entry_id"] = result["entry_id"]
    return JsonResponse(resp)
