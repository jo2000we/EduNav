from django.db import models
from django.contrib.auth.models import User


class Classroom(models.Model):
    class GroupType(models.TextChoices):
        CONTROL = "CONTROL", "Control"
        EXPERIMENTAL = "EXPERIMENTAL", "Experimental"

    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    group_type = models.CharField(max_length=12, choices=GroupType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    openai_enabled = models.BooleanField(default=False)

    class Meta:
        unique_together = ("teacher", "name")

    def save(self, *args, **kwargs):
        self.openai_enabled = self.group_type == self.GroupType.EXPERIMENTAL
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.teacher})"


class Student(models.Model):
    classroom = models.ForeignKey(
        Classroom, related_name="students", on_delete=models.CASCADE
    )
    pseudonym = models.CharField(max_length=50)
    login_code = models.CharField(max_length=20, blank=True)

    class Meta:
        unique_together = ("classroom", "pseudonym")

    def __str__(self):
        return f"{self.pseudonym} ({self.classroom.name})"
