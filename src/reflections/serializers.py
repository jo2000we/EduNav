from rest_framework import serializers
from .models import Reflection, Note

class ReflectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reflection
        fields = ["id", "user_session", "goal", "result", "obstacles", "next_step", "next_step_source", "created_at"]
        read_only_fields = ["created_at"]

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "user_session", "content", "created_at"]
        read_only_fields = ["created_at"]
