from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta


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
    max_entries_per_day = models.PositiveSmallIntegerField(
        default=1, choices=[(i, i) for i in range(1, 8)]
    )
    max_entries_per_week = models.PositiveSmallIntegerField(
        default=1, choices=[(i, i) for i in range(1, 8)]
    )

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
    overall_goal_due_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("classroom", "pseudonym")

    def __str__(self):
        return f"{self.pseudonym} ({self.classroom.name})"

    def can_create_entry(self):
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        daily_count = self.entries.filter(session_date=today).count()
        weekly_count = self.entries.filter(
            session_date__range=(week_start, week_end)
        ).count()
        return (
            daily_count < self.classroom.max_entries_per_day
            and weekly_count < self.classroom.max_entries_per_week
        )


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

class SRLEntry(models.Model):
    student = models.ForeignKey(Student, related_name="entries", on_delete=models.CASCADE)
    session_date = models.DateField(default=timezone.now)
    # Planning
    goals = models.JSONField(default=list)
    priorities = models.JSONField(default=list, blank=True)
    strategies = models.JSONField(default=list, blank=True)
    resources = models.JSONField(default=list, blank=True)
    time_planning = models.JSONField(default=list, blank=True)
    expectations = models.JSONField(default=list, blank=True)
    # Execution
    steps = models.JSONField(default=list, blank=True)
    time_usage = models.JSONField(default=list, blank=True)
    strategy_check = models.JSONField(default=list, blank=True)
    problems = models.TextField(blank=True)
    emotions = models.TextField(blank=True)
    # Reflection
    goal_achievement = models.JSONField(default=list, blank=True)
    strategy_evaluation = models.JSONField(default=list, blank=True)
    learned_subject = models.TextField(blank=True)
    learned_work = models.TextField(blank=True)
    planning_realistic = models.TextField(blank=True)
    planning_deviations = models.TextField(blank=True)
    motivation_rating = models.TextField(blank=True)
    motivation_improve = models.TextField(blank=True)
    next_phase = models.TextField(blank=True)
    strategy_outlook = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.pseudonym}: {self.session_date}"


class AppSettings(models.Model):
    """Singleton model to store application wide configuration."""

    openai_api_key = models.CharField(max_length=255, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "App Settings"
