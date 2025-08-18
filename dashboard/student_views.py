from functools import wraps
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse
from .models import Student, SRLEntry
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
        return redirect("student_login")

    pseudonym = request.POST.get("pseudonym", "").strip()
    student = Student.objects.filter(pseudonym=pseudonym).first()
    if not student:
        return HttpResponse(
            '<div class="text-red-600 mt-2">Unbekanntes Pseudonym</div>',
            status=400,
        )

    if "password1" in request.POST:
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            student.set_password(form.cleaned_data["password1"])
            student.save()
            request.session["student_id"] = student.id
            response = HttpResponse()
            response["HX-Redirect"] = reverse("student_dashboard")
            return response
        return render(
            request,
            "dashboard/partials/password_set_form.html",
            {"form": form, "pseudonym": pseudonym},
            status=400,
        )

    if "password" in request.POST:
        form = PasswordLoginForm(request.POST)
        if form.is_valid() and student.check_password(form.cleaned_data["password"]):
            request.session["student_id"] = student.id
            response = HttpResponse()
            response["HX-Redirect"] = reverse("student_dashboard")
            return response
        if form.is_valid():
            form.add_error("password", "Falsches Passwort")
        return render(
            request,
            "dashboard/partials/password_enter_form.html",
            {"form": form, "pseudonym": pseudonym},
            status=400,
        )

    if student.password:
        form = PasswordLoginForm()
        template = "dashboard/partials/password_enter_form.html"
    else:
        form = SetPasswordForm()
        template = "dashboard/partials/password_set_form.html"
    return render(
        request,
        template,
        {"form": form, "pseudonym": pseudonym},
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
    context = {
        "student": student,
        "entries": entries,
        "planning_form": PlanningForm(),
        "execution_form": ExecutionForm(),
        "reflection_form": ReflectionForm(),
        "can_create_entry": student.can_create_entry(),
    }
    return render(request, "dashboard/student_dashboard.html", context)


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
            planning_minutes = _total_minutes(entry.time_planning)
            limit = student.classroom.max_planning_execution_minutes
            if planning_minutes + usage_minutes > limit:
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
