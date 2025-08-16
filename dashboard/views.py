from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
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
            return redirect("classroom_list")
    else:
        form = ClassroomForm()
    return render(request, "dashboard/classroom_form.html", {"form": form})


@login_required
def student_list(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    students = classroom.students.all()
    return render(
        request,
        "dashboard/student_list.html",
        {"classroom": classroom, "students": students},
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
            return redirect("student_list", classroom_id=classroom.id)
    else:
        form = StudentForm()
    return render(
        request,
        "dashboard/student_form.html",
        {"form": form, "classroom": classroom},
    )

