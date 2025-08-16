from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse
from .models import Classroom, Student
from .forms import ClassroomForm, StudentForm


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
def student_list(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    if not request.headers.get("HX-Request"):
        return redirect("classroom_list")
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
        return redirect("classroom_list")
    return redirect("classroom_list")


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
        return redirect("classroom_list")
    return HttpResponse(status=405)


@login_required
def student_detail(request, classroom_id, student_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    student = get_object_or_404(Student, id=student_id, classroom=classroom)
    return render(request, "dashboard/student_detail.html", {"student": student})
