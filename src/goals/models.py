from __future__ import annotations

import uuid
from django.db import models
from django.conf import settings
from lessons.models import UserSession


class OverallGoal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="overall_goals"
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):  # pragma: no cover - simple
        return self.text[:20]


class Goal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_session = models.ForeignKey(UserSession, on_delete=models.CASCADE)
    raw_text = models.TextField()
    final_text = models.TextField(blank=True, null=True)
    smart_score = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finalized_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):  # pragma: no cover - simple
        return self.final_text or self.raw_text[:20]


class KIInteraction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="interactions")
    turn = models.IntegerField()
    role = models.CharField(max_length=20)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["turn", "created_at"]
