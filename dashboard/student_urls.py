from django.urls import path
from . import student_views

urlpatterns = [
    path("login/", student_views.student_login, name="student_login"),
    path("login/step/", student_views.student_login_step, name="student_login_step"),
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
    # API endpoints for experimental group
    path("api/entry/new/", student_views.create_entry_json, name="student_entry_create_json"),
    path(
        "api/entry/<int:entry_id>/execution/",
        student_views.add_execution_json,
        name="student_entry_execution_json",
    ),
    path(
        "api/entry/<int:entry_id>/reflection/",
        student_views.add_reflection_json,
        name="student_entry_reflection_json",
    ),
    path(
        "api/reflection/feedback/",
        student_views.reflection_feedback,
        name="reflection_feedback",
    ),
    path(
        "api/reflection/feedback/reset/",
        student_views.reset_reflection_feedback,
        name="reflection_feedback_reset",
    ),
    path(
        "api/planning/feedback/",
        student_views.planning_feedback,
        name="planning_feedback",
    ),
    path(
        "api/planning/feedback/reset/",
        student_views.reset_planning_feedback,
        name="planning_feedback_reset",
    ),
]
