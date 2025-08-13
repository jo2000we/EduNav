from __future__ import annotations

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from .models import User
from .serializers import LoginSerializer, UserSerializer
from lessons.models import LessonSession, UserSession


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pseudonym = serializer.validated_data["pseudonym"].strip()
        class_code = serializer.validated_data.get("class_code", "")
        user, created = User.objects.get_or_create(
            pseudonym=pseudonym,
            defaults={"klassengruppe": class_code or "", "gruppe": User.KG},
        )
        # Login user via session
        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)
        return Response(UserSerializer(user).data)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


@login_required
def dashboard(request):
    today = timezone.now().date()
    lesson, _ = LessonSession.objects.get_or_create(date=today)
    user_session, _ = UserSession.objects.get_or_create(user=request.user, lesson_session=lesson)
    return render(request, "dashboard.html", {"user": request.user, "user_session_id": user_session.id})


@login_required
def goal_vg_page(request):
    today = timezone.now().date()
    lesson, _ = LessonSession.objects.get_or_create(date=today)
    user_session, _ = UserSession.objects.get_or_create(user=request.user, lesson_session=lesson)
    return render(request, "goal_vg.html", {"user_session_id": user_session.id})


@login_required
def goal_kg_page(request):
    today = timezone.now().date()
    lesson, _ = LessonSession.objects.get_or_create(date=today)
    user_session, _ = UserSession.objects.get_or_create(user=request.user, lesson_session=lesson)
    return render(request, "goal_kg.html", {"user_session_id": user_session.id})


@login_required
def reflection_page(request):
    today = timezone.now().date()
    lesson, _ = LessonSession.objects.get_or_create(date=today)
    user_session, _ = UserSession.objects.get_or_create(user=request.user, lesson_session=lesson)
    return render(request, "reflection.html", {"user_session_id": user_session.id})


def login_page(request):
    if request.method == "POST":
        serializer = LoginSerializer(data=request.POST)
        if serializer.is_valid():
            pseudonym = serializer.validated_data["pseudonym"].strip()
            class_code = serializer.validated_data.get("class_code", "")
            user, _ = User.objects.get_or_create(
                pseudonym=pseudonym,
                defaults={"klassengruppe": class_code or "", "gruppe": User.KG},
            )
            user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user)
            return redirect("dashboard")
    return render(request, "login.html")
