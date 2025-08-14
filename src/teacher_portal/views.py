from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render

from config.models import SiteSettings
from lessons.models import Classroom

from .forms import ClassroomForm, SiteSettingsForm


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
    return render(
        request,
        "teacher_portal/portal.html",
        {
            "settings_form": settings_form,
            "classroom_form": classroom_form,
            "classrooms": classrooms,
        },
    )


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
