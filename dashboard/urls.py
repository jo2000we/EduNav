from django.urls import path
from . import views, export_views, visualization_views

urlpatterns = [
    path("", views.classroom_list, name="classroom_list"),
    path("classrooms/new/", views.classroom_create, name="classroom_create"),
    path("classrooms/<int:classroom_id>/students/", views.student_list, name="student_list"),
    path(
        "classrooms/<int:classroom_id>/students/new/",
        views.student_create,
        name="student_create",
    ),
    path(
        "classrooms/<int:classroom_id>/students/<int:student_id>/delete/",
        views.student_delete,
        name="student_delete",
    ),
    path(
        "classrooms/<int:classroom_id>/students/<int:student_id>/",
        views.student_detail,
        name="student_detail",
    ),
    path(
        "classrooms/<int:classroom_id>/overall-goal/",
        views.set_class_overall_goal,
        name="class_overall_goal",
    ),
    path(
        "classrooms/<int:classroom_id>/export/",
        export_views.export_classroom_data,
        name="classroom_export",
    ),
    path(
        "classrooms/<int:classroom_id>/visualize/",
        visualization_views.classroom_visualization,
        name="classroom_visualization",
    ),
    path("settings/", views.settings_view, name="settings"),
    path("settings/openai-key/", views.update_openai_key, name="update_openai_key"),
]
