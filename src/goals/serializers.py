from rest_framework import serializers
from .models import Goal, KIInteraction, OverallGoal

class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ["id", "user_session", "raw_text", "final_text", "smart_score", "created_at", "finalized_at"]
        read_only_fields = ["final_text", "smart_score", "created_at", "finalized_at"]

class KIInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = KIInteraction
        fields = ["id", "goal", "turn", "role", "content", "created_at"]
        read_only_fields = ["goal", "turn", "created_at"]


class OverallGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = OverallGoal
        fields = ["id", "text", "created_at"]
        read_only_fields = ["id", "created_at"]
