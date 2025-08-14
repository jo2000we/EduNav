from __future__ import annotations

import uuid
from django.db import models
from goals.models import Goal
from lessons.models import UserSession


class Reflection(models.Model):
    RESULT_CHOICES = [("yes", "Ja"), ("partial", "Teilweise"), ("no", "Nein")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_session = models.ForeignKey(UserSession, on_delete=models.CASCADE)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE)
    result = models.CharField(max_length=7, choices=RESULT_CHOICES)
    obstacles = models.TextField()
    next_step = models.TextField()
    next_step_source = models.CharField(max_length=10, default="user")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["goal"], name="unique_reflection_per_goal"
            )
        ]
