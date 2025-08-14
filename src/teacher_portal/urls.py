from django.urls import path

from . import views

app_name = "teacher_portal"

urlpatterns = [
    path("", views.portal, name="portal"),
]
