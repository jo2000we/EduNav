"""EduNav URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from exports.admin import DashboardView
from accounts.views import (
    login_page,
    dashboard,
    goal_vg_page,
    goal_kg_page,
    reflection_page,
)

urlpatterns = [
    path("admin/exports/dashboard/", DashboardView.as_view(), name="exports-dashboard"),
    path("admin/", admin.site.urls),
    path("", login_page, name="login"),
    path("dashboard/", dashboard, name="dashboard"),
    path("goal/vg/", goal_vg_page, name="goal_vg"),
    path("goal/kg/", goal_kg_page, name="goal_kg"),
    path("reflection/", reflection_page, name="reflection"),
    path("api/", include("accounts.urls")),
    path("api/", include("lessons.urls")),
    path("api/", include("goals.urls")),
    path("api/", include("reflections.urls")),
    path("api/", include("exports.urls")),
]
