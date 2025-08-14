from rest_framework import serializers
from .models import LessonSession, UserSession


class LessonSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonSession
        fields = ["id", "date", "topic", "period", "classroom", "use_ai"]


class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = ["id", "user", "lesson_session", "started_at", "ended_at"]
        read_only_fields = ["started_at", "ended_at"]
