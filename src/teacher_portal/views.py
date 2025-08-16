from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.models import User
from config.models import SiteSettings
from lessons.models import Classroom

from .forms import (
    BulkStudentsForm,
    ClassroomForm,
    SiteSettingsForm,
    StudentForm,
)


@staff_member_required
def portal(request):
    settings_obj = SiteSettings.get()
    settings_form = SiteSettingsForm(instance=settings_obj)
    classroom_form = ClassroomForm()

    if request.method == "POST":
        if "save_settings" in request.POST:
            settings_form = SiteSettingsForm(request.POST, instance=settings_obj)
            if settings_form.is_valid():
                settings_form.save()
                return redirect("teacher_portal:portal")
        elif "add_classroom" in request.POST:
            classroom_form = ClassroomForm(request.POST)
            if classroom_form.is_valid():
                classroom_form.save()
                return redirect("teacher_portal:portal")

    classrooms = Classroom.objects.all()
    check_openai_key_url = reverse("teacher_portal:check_openai_key")
    openai_attrs = {
        "hx-post": check_openai_key_url,
        "hx-trigger": "keyup changed delay:500ms",
        "hx-target": "closest div",
        "hx-swap": "none",
        "value": settings_form["openai_api_key"].value() or "",
    }
    return render(
        request,
        "teacher_portal/portal.html",
        {
            "settings_form": settings_form,
            "classroom_form": classroom_form,
            "classrooms": classrooms,
            "openai_attrs": openai_attrs,
        },
    )


@staff_member_required
def check_openai_key(request):
    form = SiteSettingsForm(request.POST)
    if form.is_valid():
        return HttpResponse("OK")
    return HttpResponse("Invalid", status=400)


@staff_member_required
def edit_classroom(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk)
    if request.method == "POST":
        form = ClassroomForm(request.POST, instance=classroom)
        if form.is_valid():
            form.save()
            return redirect("teacher_portal:portal")
    else:
        form = ClassroomForm(instance=classroom)
    return render(
        request,
        "teacher_portal/edit_classroom.html",
        {"form": form, "classroom": classroom},
    )


@staff_member_required
def delete_classroom(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk)
    if request.method == "POST":
        classroom.delete()
    return redirect("teacher_portal:portal")


@staff_member_required
def regenerate_classroom_code(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk)
    if request.method == "POST":
        classroom.code = None
        classroom.save()
    return redirect("teacher_portal:portal")


@staff_member_required
def classroom_students(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk)
    students = User.objects.filter(classroom=classroom).order_by("pseudonym")
    form = BulkStudentsForm()
    if request.method == "POST":
        form = BulkStudentsForm(request.POST, request.FILES)
        if form.is_valid():
            gruppe = form.cleaned_data["gruppe"]
            for pseudonym in form.cleaned_data["pseudonym_list"]:
                User.objects.create_user(
                    pseudonym=pseudonym, classroom=classroom, gruppe=gruppe
                )
            return redirect("teacher_portal:classroom_students", pk=classroom.pk)
    return render(
        request,
        "teacher_portal/classroom_students.html",
        {"classroom": classroom, "students": students, "form": form},
    )


@staff_member_required
def edit_student(request, pk):
    student = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect(
                "teacher_portal:classroom_students", pk=student.classroom_id
            )
    else:
        form = StudentForm(instance=student)
    return render(
        request,
        "teacher_portal/edit_student.html",
        {"form": form, "student": student},
    )


@staff_member_required
def delete_student(request, pk):
    student = get_object_or_404(User, pk=pk)
    classroom_pk = student.classroom_id
    if request.method == "POST":
        student.delete()
    return redirect("teacher_portal:classroom_students", pk=classroom_pk)
