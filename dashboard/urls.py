from django.urls import path
from . import views

urlpatterns = [
    path("", views.classroom_list, name="classroom_list"),
    path("classrooms/new/", views.classroom_create, name="classroom_create"),
    path("classrooms/<int:classroom_id>/students/", views.student_list, name="student_list"),
    path(
        "classrooms/<int:classroom_id>/students/new/",
        views.student_create,
        name="student_create",
    ),
]
