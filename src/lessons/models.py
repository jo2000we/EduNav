from __future__ import annotations

import uuid
from django.db import models
from django.conf import settings


class Classroom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True, null=True, unique=True)
    use_ai = models.BooleanField(default=False)

    def __str__(self) -> str:  # pragma: no cover - simple
        return self.name

class LessonSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    topic = models.CharField(max_length=200, blank=True)
    period = models.IntegerField(null=True, blank=True)
    classroom = models.ForeignKey(Classroom, null=True, blank=True, on_delete=models.SET_NULL)
    use_ai = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.use_ai is None:
            if self.classroom:
                self.use_ai = self.classroom.use_ai
            else:
                self.use_ai = False
        super().save(*args, **kwargs)

    def __str__(self):  # pragma: no cover - simple
        return f"{self.date} {self.topic}".strip()


class UserSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson_session = models.ForeignKey(LessonSession, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "lesson_session")
