from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from .models import Student, SRLEntry
from .forms import (
    StudentLoginForm,
    OverallGoalForm,
    PlanningForm,
    ExecutionForm,
    ReflectionForm,
)


def student_login(request):
    if request.method == "POST":
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            pseudonym = form.cleaned_data["pseudonym"]
            try:
                student = Student.objects.get(pseudonym=pseudonym)
                request.session["student_id"] = student.id
                return redirect("student_dashboard")
            except Student.DoesNotExist:
                form.add_error("pseudonym", "Unbekanntes Pseudonym")
    else:
        form = StudentLoginForm()
    return render(request, "dashboard/student_login.html", {"form": form})


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
        "overall_goal_form": OverallGoalForm(instance=student),
        "planning_form": PlanningForm(),
        "execution_form": ExecutionForm(),
        "reflection_form": ReflectionForm(),
    }
    return render(request, "dashboard/student_dashboard.html", context)


@student_required
def update_overall_goal(request):
    student = Student.objects.get(id=request.session["student_id"])
    if request.method == "POST":
        form = OverallGoalForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
    return redirect("student_dashboard")


@student_required
def create_entry(request):
    student = Student.objects.get(id=request.session["student_id"])
    if request.method == "POST":
        form = PlanningForm(request.POST)
        if form.is_valid():
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
