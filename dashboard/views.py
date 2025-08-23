from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
import json
import requests

from .models import Classroom, Student, AppSettings
from .forms import (
    ClassroomForm,
    StudentForm,
    ClassOverallGoalForm,
    ClassEntryLimitForm,
    ClassTimeLimitForm,
)


@login_required
def classroom_list(request):
    classrooms = Classroom.objects.filter(teacher=request.user)
    return render(request, "dashboard/classroom_list.html", {"classrooms": classrooms})


@login_required
def classroom_create(request):
    if request.method == "POST":
        form = ClassroomForm(request.POST)
        if form.is_valid():
            classroom = form.save(commit=False)
            classroom.teacher = request.user
            classroom.save()
            if request.headers.get("HX-Request"):
                response = HttpResponse()
                response["HX-Redirect"] = reverse("classroom_list")
                return response
            return redirect("classroom_list")
    else:
        form = ClassroomForm()
    return render(request, "dashboard/classroom_form.html", {"form": form})


@login_required
def set_class_overall_goal(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    first_student = classroom.students.first()
    initial = {}
    if first_student:
        initial = {
            "overall_goal": first_student.overall_goal or "",
            "overall_goal_due_date": first_student.overall_goal_due_date,
        }
    if request.method == "POST":
        form = ClassOverallGoalForm(request.POST)
        if form.is_valid():
            goal = form.cleaned_data["overall_goal"]
            due = form.cleaned_data["overall_goal_due_date"]
            classroom.students.update(overall_goal=goal, overall_goal_due_date=due)
            if request.headers.get("HX-Request"):
                response = HttpResponse()
                response["HX-Redirect"] = reverse("classroom_list")
                return response
            return redirect("classroom_list")
    else:
        form = ClassOverallGoalForm(initial=initial)
    if request.headers.get("HX-Request"):
        return render(
            request,
            "dashboard/class_overall_goal_form.html",
            {"form": form, "classroom": classroom},
        )
    return redirect("classroom_list")


@login_required
def set_class_entry_limits(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    if request.method == "POST":
        form = ClassEntryLimitForm(request.POST, instance=classroom)
        if form.is_valid():
            form.save()
            if request.headers.get("HX-Request"):
                response = HttpResponse()
                response["HX-Redirect"] = reverse("classroom_list")
                return response
            return redirect("classroom_list")
    else:
        form = ClassEntryLimitForm(instance=classroom)
    if request.headers.get("HX-Request"):
        return render(
            request,
            "dashboard/class_entry_limits_form.html",
            {"form": form, "classroom": classroom},
        )
    return redirect("classroom_list")


@login_required
def set_class_time_limit(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    if request.method == "POST":
        form = ClassTimeLimitForm(request.POST, instance=classroom)
        if form.is_valid():
            form.save()
            if request.headers.get("HX-Request"):
                response = HttpResponse()
                response["HX-Redirect"] = reverse("classroom_list")
                return response
            return redirect("classroom_list")
    else:
        form = ClassTimeLimitForm(instance=classroom)
    if request.headers.get("HX-Request"):
        return render(
            request,
            "dashboard/class_time_limit_form.html",
            {"form": form, "classroom": classroom},
        )
    return redirect("classroom_list")


@login_required
def student_list(request, classroom_id):
    if not request.headers.get("HX-Request"):
        return redirect("classroom_list")
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    students = classroom.students.all()
    form = StudentForm()
    return render(
        request,
        "dashboard/student_list.html",
        {"classroom": classroom, "students": students, "form": form},
    )


@login_required
def student_create(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.classroom = classroom
            student.save()
            if request.headers.get("HX-Request"):
                students = classroom.students.all()
                form = StudentForm()
                return render(
                    request,
                    "dashboard/student_list.html",
                    {"classroom": classroom, "students": students, "form": form},
                )
            return redirect("student_list", classroom_id=classroom.id)
    else:
        form = StudentForm()
    students = classroom.students.all()
    return render(
        request,
        "dashboard/student_list.html",
        {"classroom": classroom, "students": students, "form": form},
    )


@login_required
def student_delete(request, classroom_id, student_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    student = get_object_or_404(Student, id=student_id, classroom=classroom)
    if request.method == "POST":
        student.delete()
        if request.headers.get("HX-Request"):
            students = classroom.students.all()
            form = StudentForm()
            return render(
                request,
                "dashboard/student_list.html",
                {"classroom": classroom, "students": students, "form": form},
            )
        return redirect("student_list", classroom_id=classroom.id)
    return HttpResponse(status=405)


@login_required
def student_reset_password(request, classroom_id, student_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    student = get_object_or_404(Student, id=student_id, classroom=classroom)
    student.password = ""
    student.save(update_fields=["password"])
    if request.headers.get("HX-Request"):
        students = classroom.students.all()
        form = StudentForm()
        return render(
            request,
            "dashboard/student_list.html",
            {"classroom": classroom, "students": students, "form": form},
        )
    return redirect("student_list", classroom_id=classroom.id)


@login_required
def student_detail(request, classroom_id, student_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    student = get_object_or_404(Student, id=student_id, classroom=classroom)
    entries = student.entries.order_by("-session_date")
    return render(
        request,
        "dashboard/student_detail.html",
        {"student": student, "entries": entries},
    )


def validate_openai_key(key: str) -> bool:
    if not key:
        return False
    try:
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=5,
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


@login_required
def settings_view(request):
    settings = AppSettings.load()
    key_valid = validate_openai_key(settings.openai_api_key)
    return render(
        request,
        "dashboard/settings.html",
        {"settings": settings, "key_valid": key_valid},
    )


@login_required
@require_POST
def update_openai_key(request):
    data = json.loads(request.body.decode("utf-8"))
    key = data.get("openai_api_key", "")
    settings = AppSettings.load()
    settings.openai_api_key = key
    settings.save()
    valid = validate_openai_key(key)
    return JsonResponse({"valid": valid})


@login_required
@require_POST
def update_openai_model(request):
    data = json.loads(request.body.decode("utf-8"))
    model = data.get("openai_model") or "gpt-4o-mini"
    settings = AppSettings.load()
    settings.openai_model = model
    settings.save()
    return JsonResponse({})
