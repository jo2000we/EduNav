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
    api_key = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        unique_together = ("teacher", "name")

    def save(self, *args, **kwargs):
        self.openai_enabled = self.group_type == self.GroupType.EXPERIMENTAL
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Student(models.Model):
    classroom = models.ForeignKey(
        Classroom, related_name="students", on_delete=models.CASCADE
    )

    pseudonym = models.CharField(max_length=50)
    login_code = models.CharField(max_length=20, blank=True)
    overall_goal = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("classroom", "pseudonym")

    def __str__(self):
        return f"{self.pseudonym} ({self.classroom.name})"


class LearningGoal(models.Model):
    student = models.ForeignKey(
        Student, related_name="goals", on_delete=models.CASCADE
    )
    text = models.TextField()
    session_date = models.DateField()
    achieved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.pseudonym}: {self.text[:50]}"

class DayEntry(models.Model):
    student = models.ForeignKey(
        Student, related_name="entries", on_delete=models.CASCADE
    )
    session_date = models.DateField()
    strategies = models.TextField(blank=True)
    resources = models.TextField(blank=True)
    expectations = models.TextField(blank=True)
    steps = models.TextField(blank=True)
    strategy_check = models.TextField(blank=True)
    problems = models.TextField(blank=True)
    emotions_execution = models.TextField(blank=True)
    strategy_evaluation = models.TextField(blank=True)
    self_assessment = models.TextField(blank=True)
    time_management_reflection = models.TextField(blank=True)
    emotions_reflection = models.TextField(blank=True)
    outlook = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.pseudonym}: {self.session_date}"


class Goal(models.Model):
    class Achievement(models.TextChoices):
        FULL = "vollständig", "vollständig"
        PARTIAL = "teilweise", "teilweise"
        NONE = "nicht", "nicht"

    entry = models.ForeignKey(
        DayEntry, related_name="goals", on_delete=models.CASCADE
    )
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    high_priority = models.BooleanField(default=False)
    planned_time = models.DurationField(default=0)
    engaged = models.BooleanField(default=False)
    actual_time = models.DurationField(default=0)
    achievement = models.CharField(
        max_length=20, choices=Achievement.choices, blank=True
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.text[:50]}"

    @property
    def planned_time_hhmm(self) -> str:
        total_minutes = int(self.planned_time.total_seconds() // 60)
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"

    @property
    def actual_time_hhmm(self) -> str:
        total_minutes = int(self.actual_time.total_seconds() // 60)
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
