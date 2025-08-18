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
    # Chatbot endpoints for experimental group
    path("api/chat/planning/", student_views.chat_planning, name="chat_planning"),
    path(
        "api/chat/execution/<int:entry_id>/",
        student_views.chat_execution,
        name="chat_execution",
    ),
    path(
        "api/chat/reflection/<int:entry_id>/",
        student_views.chat_reflection,
        name="chat_reflection",
    ),
]
