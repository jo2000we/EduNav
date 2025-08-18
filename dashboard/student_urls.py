from django.urls import path
from . import student_views

urlpatterns = [
    path("login/", student_views.student_login, name="student_login"),
    path("logout/", student_views.student_logout, name="student_logout"),
    path("dashboard/", student_views.student_dashboard, name="student_dashboard"),
    path("entry/new/", student_views.create_entry, name="student_entry_create"),
    path(
        "entry/<int:entry_id>/execution/",
        student_views.add_execution,
        name="student_entry_execution",
    ),
    path(
        "entry/<int:entry_id>/reflection/",
        student_views.add_reflection,
        name="student_entry_reflection",
    ),
]
