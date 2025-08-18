from functools import wraps
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Student, SRLEntry
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import json
from django.urls import reverse
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
        return JsonResponse({"status": "ok"})
    return JsonResponse({"errors": form.errors}, status=400)
