from django.urls import path

from . import views

app_name = "teacher_portal"

urlpatterns = [
    path("", views.portal, name="portal"),
    path("classroom/<uuid:pk>/edit/", views.edit_classroom, name="edit_classroom"),
    path("classroom/<uuid:pk>/delete/", views.delete_classroom, name="delete_classroom"),
    path(
        "classroom/<uuid:pk>/regenerate/",
        views.regenerate_classroom_code,
        name="regenerate_classroom_code",
    ),
]
