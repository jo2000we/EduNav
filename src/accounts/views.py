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
from lessons.models import LessonSession, UserSession, Classroom
from goals.models import Goal, OverallGoal
from reflections.models import Reflection
from config.models import SiteSettings


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pseudonym = serializer.validated_data["pseudonym"].strip()
        class_code = serializer.validated_data.get("class_code", "").strip()
        classroom = None
        if class_code:
            try:
                classroom = Classroom.objects.get(code=class_code)
            except Classroom.DoesNotExist:
                return Response(
                    {"class_code": ["Classroom not found."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        try:
            user = User.objects.get(pseudonym=pseudonym)
        except User.DoesNotExist:
            return Response(
                {"pseudonym": ["User not found."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if classroom and user.classroom != classroom:
            user.classroom = classroom
            user.save()
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
    lesson, _ = LessonSession.objects.get_or_create(date=today, classroom=request.user.classroom)
    user_session, _ = UserSession.objects.get_or_create(user=request.user, lesson_session=lesson)
    can_use_ai = (
        request.user.gruppe == User.VG
        and lesson.use_ai
        and SiteSettings.get().allow_ai
    )
    goals = (
        Goal.objects
        .filter(user_session__user=request.user)
        .select_related("user_session__lesson_session")
        .prefetch_related("reflection_set")
        .order_by("-created_at")[:5]
    )
    overall_goal = OverallGoal.objects.filter(user=request.user).first()
    if overall_goal:
        goals_since = Goal.objects.filter(
            user_session__user=request.user,
            created_at__gte=overall_goal.created_at,
        )
        completed = (
            Reflection.objects.filter(goal__in=goals_since, result="yes").count()
        )
        total = goals_since.count()
    else:
        completed = total = 0
    open_goals = total - completed
    completion_rate = int(completed / total * 100) if total else 0
    return render(
        request,
        "dashboard.html",
        {
            "user": request.user,
            "user_session_id": user_session.id,
            "can_use_ai": can_use_ai,
            "goals": goals,
            "overall_goal": overall_goal,
            "completed_goals": completed,
            "open_goals": open_goals,
            "completion_rate": completion_rate,
        },
    )


@login_required
def goal_vg_page(request):
    today = timezone.now().date()
    lesson, _ = LessonSession.objects.get_or_create(date=today, classroom=request.user.classroom)
    user_session, _ = UserSession.objects.get_or_create(user=request.user, lesson_session=lesson)
    return render(request, "goal_vg.html", {"user_session_id": user_session.id})


@login_required
def goal_kg_page(request):
    today = timezone.now().date()
    lesson, _ = LessonSession.objects.get_or_create(date=today, classroom=request.user.classroom)
    user_session, _ = UserSession.objects.get_or_create(user=request.user, lesson_session=lesson)
    return render(request, "goal_kg.html", {"user_session_id": user_session.id})


@login_required
def overall_goal_page(request):
    goal = OverallGoal.objects.filter(user=request.user).first()
    return render(request, "overall_goal.html", {"goal": goal})


@login_required
def reflection_page(request):
    today = timezone.now().date()
    lesson, _ = LessonSession.objects.get_or_create(date=today, classroom=request.user.classroom)
    user_session, _ = UserSession.objects.get_or_create(user=request.user, lesson_session=lesson)
    goal = Goal.objects.filter(user_session=user_session).first()
    can_use_ai = (
        request.user.gruppe == User.VG
        and lesson.use_ai
        and SiteSettings.get().allow_ai
    )
    context = {
        "user_session_id": user_session.id,
        "goal_id": getattr(goal, "id", ""),
        "can_use_ai": can_use_ai,
    }
    return render(request, "reflection.html", context)


def login_page(request):
    error = ""
    if request.method == "POST":
        serializer = LoginSerializer(data=request.POST)
        if serializer.is_valid():
            pseudonym = serializer.validated_data["pseudonym"].strip()
            class_code = serializer.validated_data.get("class_code", "").strip()
            classroom = None
            if class_code:
                try:
                    classroom = Classroom.objects.get(code=class_code)
                except Classroom.DoesNotExist:
                    error = "Klasse existiert nicht."
            if not error:
                try:
                    user = User.objects.get(pseudonym=pseudonym)
                    if classroom and user.classroom != classroom:
                        user.classroom = classroom
                        user.save()
                    user.backend = "django.contrib.auth.backends.ModelBackend"
                    login(request, user)
                    return redirect("dashboard")
                except User.DoesNotExist:
                    error = "Benutzer nicht gefunden."
    return render(request, "login.html", {"error": error})
