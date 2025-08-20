from functools import wraps
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Student, SRLEntry, AppSettings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import json
from django.urls import reverse
import requests
from .export_views import _entry_nested
from .forms import (
    PseudoForm,
    PasswordLoginForm,
    SetPasswordForm,
    PlanningForm,
    ExecutionForm,
    ReflectionForm,
)


def _total_minutes(items):
    total = 0
    for item in items:
        t = item.get("time")
        if not t:
            continue
        try:
            hours, minutes = [int(x) for x in t.split(":")]
            total += hours * 60 + minutes
        except (ValueError, AttributeError):
            continue
    return total


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
            if planning_minutes > limit:
                messages.error(
                    request,
                    f"Die Gesamtzeit darf {limit} Minuten nicht überschreiten.",
                )
            else:
                entry = form.save(commit=False)
                entry.student = student
                entry.save()
                request.session.pop("planning_ai_messages", None)
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
            if usage_minutes > limit:
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
            request.session.pop("reflection_ai_messages", None)
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
        if planning_minutes > limit:
            return JsonResponse(
                {"error": f"Die Gesamtzeit darf {limit} Minuten nicht überschreiten."},
                status=400,
            )
        entry = form.save(commit=False)
        entry.student = student
        entry.save()
        request.session.pop("planning_ai_messages", None)
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
      "strategy_check": [{"strategy": "str", "used": bool, "useful": bool, "change": "str"}, ...],
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
        if usage_minutes > limit:
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
      "goal_achievement": [{"achievement": "str", "comment": "str"}, ...],
      "strategy_evaluation": [{"helpful": bool, "comment": "str", "reuse": bool}, ...],
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

    form_data = {
        "goal_achievement": json.dumps(payload.get("goal_achievement", [])),
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
        request.session.pop("reflection_ai_messages", None)
        return JsonResponse({"status": "ok"})
    return JsonResponse({"errors": form.errors}, status=400)


@student_required
@require_POST
def planning_feedback(request):
    student = Student.objects.get(id=request.session["student_id"])
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    planning = payload.get("planning", {})
    entries = student.entries.order_by("session_date")
    diary = {
        "Gesamtziel": student.overall_goal,
        "Fälligkeitsdatum des Gesamtziels": student.overall_goal_due_date.isoformat()
        if student.overall_goal_due_date
        else None,
        "Einträge": [_entry_nested(e) for e in entries],
    }

    base_prompt = (
        "Rolle des KI-Assistenten:\n"
        "Du bist ein Lerncoach, der einen Schüler während einer mehrwöchigen Projektarbeit unterstützt. "
        "Der Schüler führt ein selbstreguliertes Lerntagebuch, in dem er seine Lernprozesse dokumentiert. "
        "Deine Aufgabe ist es, konstruktives, wissenschaftlich fundiertes Feedback zu seiner aktuellen Planung zu geben, "
        "um ihn bei der Entwicklung von Selbstregulationsfähigkeiten zu unterstützen.\n"
        "Eingabedaten:\n"
        f"-> Das derzeitige SRL Tagebuch: {json.dumps(diary, ensure_ascii=False)}\n"
        f"-> Der aktuelle Planungsentwurf des Schülers {json.dumps(planning, ensure_ascii=False)}\n"
        "Hinweise:\n"
        "Das Lerntagebuch kann auch leer sein (falls dies der erste Eintrag ist).\n"
        "Die Planung enthält Ziele, Prioritäten (Reihenfolge der Ziele in der sie bearbeitet werden sollen + Markierung besonders wichtiger Ziele), Strategien, Ressourcen, Zeitplanung (wie viel Zeit pro Ziel eingeplant wurde) und Erwartungen (Erwartungen geben an, woran der Schüler festlegt dass das Ziel erreicht wurde).\n"
        "Aufgabe des KI-Assistenten\n"
        "Analysiere alle vorliegenden Informationen:\n"
        "Projektkontext (Gesamtziel + Frist)\n"
        "Vergangene Lerntagebuch-Einträge (falls vorhanden → Rückbezug auf Erfahrungen, erfolgreiche oder problematische Strategien)\n"
        "Aktuelle Planung (Ziele, Prioritäten, Strategien, Ressourcen, Zeitplanung, Erfolgskriterien)\n"
        "Regeln für dein Feedback (wissenschaftlich gestützt)\n"
        "Autonomie-Support (Selbstbestimmungstheorie)\n"
        "Gib keine fertigen Lösungen vor.\n"
        "Stelle reflektierende Fragen („Wie realistisch ist dein Zeitplan im Vergleich zu früher?“) und biete Optionen statt Anweisungen.\n"
        "Informativ, nicht wertend\n"
        "Kein einfaches „gut“ oder „schlecht“.\n"
        "Stattdessen sachliche Rückmeldung mit Verbesserungsvorschlägen („Dein Ziel ist klar formuliert – vielleicht könntest du noch konkretisieren, wie du den Fortschritt überprüfst“).\n"
        "Ressourcen- und Stärkenorientierung\n"
        "Betone positive Elemente („Du hast dir mehrere Strategien notiert – das zeigt, dass du vorbereitet bist“).\n"
        "Gib Hinweise, wie vorhandene Ressourcen sinnvoller eingesetzt werden können.\n"
        "Metakognition anregen\n"
        "Stelle Fragen, die den Schüler zum Nachdenken über seine eigenen Entscheidungen bringen („Welche dieser Strategien hat dir in der Vergangenheit am meisten geholfen?“).\n"
        "Realistische Planung prüfen\n"
        "Prüfe, ob Zeitaufwand und Strategien im Verhältnis zum Gesamtziel stehen.\n"
        "Hebe Widersprüche oder Überlastung hervor („Du hast 3 Tage für Recherche eingeplant, aber noch 4 Wochen bis zur Abgabe – wäre eine Verteilung sinnvoll?“).\n"
        "Verknüpfung mit der Vergangenheit\n"
        "Falls es Tagebuch-Einträge gibt: beziehe dich aktiv auf sie („Beim letzten Mal hast du geschrieben, dass dich Ablenkungen gestört haben – wie berücksichtigst du das diesmal in deiner Planung?“).\n"
        "Förderung von Reflexion und Anpassung\n"
        "Fordere den Schüler am Ende des Feedbacks auf, seine Planung bei Bedarf selbstständig zu überarbeiten.\n"
        "Erwartete Ausgabe\n"
        "Formuliere dein Feedback als klar verständlichen Fließtext mit folgenden Komponenten:\n"
        "Kurze positive Würdigung der aktuellen Planung.\n"
        "Konkret-informative Rückmeldungen zu den Bereichen Ziele, Strategien, Ressourcen, Zeitplanung und Erfolgskriterien.\n"
        "Reflektierende Fragen, die den Schüler zum Überarbeiten anregen.\n"
        "Abschließende Bestärkung, dass der Schüler durch kleine Anpassungen noch besser sein Ziel erreichen kann."
    )

    messages = request.session.get("planning_ai_messages")
    if not messages:
        messages = [{"role": "user", "content": base_prompt}]
    else:
        followup = (
            "Der Schüler hat nun einen zweiten Entwurf eingereicht "
            f"{json.dumps(planning, ensure_ascii=False)} "
            "gebe erneut Feedback nach den gleichen Richtlinien wie zuvor. Hebe dabei positive Veränderungen der Planung seit der letzten Version hervor."
        )
        messages.append({"role": "user", "content": followup})

    settings = AppSettings.load()
    if not settings.openai_api_key:
        return JsonResponse({"error": "Kein OpenAI API Key hinterlegt."}, status=400)

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": "gpt-4o-mini", "messages": messages},
            timeout=30,
        )
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"]
    except requests.RequestException:
        return JsonResponse({"error": "Fehler bei der Verbindung zur OpenAI API."}, status=500)

    messages.append({"role": "assistant", "content": reply})
    request.session["planning_ai_messages"] = messages
    return JsonResponse({"feedback": reply})


@student_required
@require_POST
def reset_planning_feedback(request):
    request.session.pop("planning_ai_messages", None)
    return JsonResponse({"status": "ok"})


@student_required
@require_POST
def reflection_feedback(request):
    student = Student.objects.get(id=request.session["student_id"])
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    reflection = payload.get("reflection", {})
    entries = student.entries.order_by("session_date")
    entry = entries.last()
    if not entry:
        return JsonResponse({"error": "Kein Eintrag vorhanden"}, status=404)
    diary = {
        "Gesamtziel": student.overall_goal,
        "Fälligkeitsdatum des Gesamtziels": student.overall_goal_due_date.isoformat()
        if student.overall_goal_due_date
        else None,
        "Einträge": [_entry_nested(e) for e in entries],
    }

    current = _entry_nested(entry)
    plan_exec = {
        "Planung": current.get("Planung"),
        "Durchführung": current.get("Durchführung"),
    }

    base_prompt = (
        "Rolle des KI-Assistenten:\n"
        "Du bist ein Lerncoach, der einen Schüler während einer mehrwöchigen Projektarbeit unterstützt. "
        "Der Schüler führt ein selbstreguliertes Lerntagebuch, in dem er seine Lernprozesse dokumentiert. "
        "Jetzt bewertet der Schüler seine Reflexion zur abgeschlossenen Arbeitsphase. Deine Aufgabe ist es, "
        "konstruktives, wissenschaftlich fundiertes Feedback zu dieser Reflexion zu geben, um den Schüler bei "
        "der Entwicklung seiner Selbstregulationsfähigkeiten zu unterstützen.\n"
        f"-> SRL Tagebuch (der aktuelle Eintrag ist der, wo Planung und Durchführung vorhanden sind, aber Reflexion fehlt und das Datum am aktuellsten ist): {json.dumps(diary, ensure_ascii=False)}\n"
        f"-> Planung und Durchführung des aktuellen Eintrags: {json.dumps(plan_exec, ensure_ascii=False)}\n"
        f"-> Der aktuelle Reflexionsentwurf des Schülers: {json.dumps(reflection, ensure_ascii=False)}\n"
        "Aufgabe des KI-Assistenten\n"
        "Analysiere alle vorliegenden Informationen:\n"
        "Projektkontext (Gesamtziel + Frist)\n"
        "Bisherige Tagebuch-Einträge und Planung (inkl. geplante Ziele, Strategien, Zeitmanagement)\n"
        "Aktuelle Reflexion (Zielerreichung, Strategien, Lernen, Zeitmanagement, Motivation, Ausblick)\n"
        "Beachte besonders: Widersprüche und Inkonsistenzen (z. B. „Zeitplan war realistisch“ vs. „große Abweichungen in der Umsetzung“).\n"
        "Regeln für dein Feedback (wissenschaftlich gestützt)\n"
        "Autonomie-Support (Selbstbestimmungstheorie)\n"
        "Stelle offene, reflektierende Fragen, die den Schüler zum eigenen Nachdenken und Anpassen anregen.\n"
        "Keine Anweisungen, sondern Impulse: „Wie erklärst du dir…?“, „Welche Alternativen siehst du…?“\n"
        "Informativ, nicht wertend\n"
        "Kein einfaches „gut/schlecht“.\n"
        "Stattdessen sachliche Rückmeldungen mit konkreten Hinweisen: „Du hast deine Motivation als schwankend beschrieben – welche Strategien haben dir trotzdem geholfen, dranzubleiben?“\n"
        "Ressourcen- und Stärkenorientierung\n"
        "Anerkenne positive Entwicklungen („Du hast erkannt, dass dir Brainstorming geholfen hat – das zeigt, dass du deine Strategien gut reflektierst“).\n"
        "Hebe Fortschritte hervor (z. B. verbesserte Planung im Vergleich zum Vorherigen).\n"
        "Metakognition anregen\n"
        "Stelle Fragen, die den Schüler dazu bringen, über eigene Denk- und Lernprozesse nachzudenken: „Was bedeutet es für dich, dass eine Strategie teilweise geholfen hat?“\n"
        "Inkonsistenzen ansprechen\n"
        "Identifiziere mögliche Widersprüche zwischen Planung, Umsetzung und Reflexion (z. B. „Du hast deine Planung als realistisch eingeschätzt, aber schreibst gleichzeitig, dass du stark vom Plan abgewichen bist – wie passt das für dich zusammen?“).\n"
        "Stelle Nachfragen, ohne belehrend zu wirken.\n"
        "Ausblick unterstützen\n"
        "Hilf dem Schüler, aus seiner Reflexion konkrete nächste Schritte abzuleiten.\n"
        "Stelle Fragen wie: „Welche deiner beschriebenen Strategien würdest du jetzt priorisieren?“ oder „Wie kannst du deine Motivation gezielt stärken?“\n"
        "Erwartete Ausgabe\n"
        "Formuliere dein Feedback als klar verständlichen Fließtext mit den folgenden Abschnitten:\n"
        "Positives (Würdigung von Fortschritten und gelungenen Reflexionselementen)\n"
        "Konkret-informative Hinweise (Ziele, Strategien, Zeitmanagement, Motivation, Konsistenz)\n"
        "Reflektierende Fragen (die den Schüler zum Weiterdenken und Anpassen anregen)\n"
        "Bestärkung (ermutigendes Fazit: kleine Anpassungen führen zu mehr Selbstregulation)"
    )

    messages = request.session.get("reflection_ai_messages")
    if not messages:
        messages = [{"role": "user", "content": base_prompt}]
    else:
        followup = (
            "Der Schüler hat nun einen zweiten Entwurf eingereicht "
            f"{json.dumps(reflection, ensure_ascii=False)} "
            "gebe erneut Feedback nach den gleichen Richtlinien wie zuvor. Hebe dabei positive Veränderungen der Reflexion seit der letzten Version hervor."
        )
        messages.append({"role": "user", "content": followup})

    settings = AppSettings.load()
    if not settings.openai_api_key:
        return JsonResponse({"error": "Kein OpenAI API Key hinterlegt."}, status=400)

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": "gpt-4o-mini", "messages": messages},
            timeout=30,
        )
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"]
    except requests.RequestException:
        return JsonResponse({"error": "Fehler bei der Verbindung zur OpenAI API."}, status=500)

    messages.append({"role": "assistant", "content": reply})
    request.session["reflection_ai_messages"] = messages
    return JsonResponse({"feedback": reply})


@student_required
@require_POST
def reset_reflection_feedback(request):
    request.session.pop("reflection_ai_messages", None)
    return JsonResponse({"status": "ok"})
