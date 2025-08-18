import json
from datetime import timedelta

import pytest
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from dashboard.models import Classroom, Student, SRLEntry


@pytest.mark.django_db
def test_can_create_entry_daily_limit():
    teacher = User.objects.create(username="t1")
    classroom = Classroom.objects.create(
        teacher=teacher,
        name="Klasse A",
        group_type="CONTROL",
        max_entries_per_day=1,
        max_entries_per_week=7,
    )
    student = Student.objects.create(classroom=classroom, pseudonym="S1")
    SRLEntry.objects.create(student=student, session_date=timezone.now().date())
    assert student.can_create_entry() is False


@pytest.mark.django_db
def test_can_create_entry_weekly_limit():
    teacher = User.objects.create(username="t1")
    classroom = Classroom.objects.create(
        teacher=teacher,
        name="Klasse A",
        group_type="CONTROL",
        max_entries_per_day=7,
        max_entries_per_week=2,
    )
    student = Student.objects.create(classroom=classroom, pseudonym="S1")
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    SRLEntry.objects.create(student=student, session_date=week_start)
    SRLEntry.objects.create(student=student, session_date=week_start + timedelta(days=1))
    assert student.can_create_entry() is False


@pytest.mark.django_db
def test_create_entry_respects_limits(client):
    teacher = User.objects.create(username="t1")
    classroom = Classroom.objects.create(
        teacher=teacher,
        name="Klasse A",
        group_type="CONTROL",
        max_entries_per_day=1,
        max_entries_per_week=1,
    )
    student = Student.objects.create(classroom=classroom, pseudonym="S1")
    session = client.session
    session["student_id"] = student.id
    session.save()
    data = {
        "goals": json.dumps(["a"]),
        "priorities": json.dumps([{"goal": "a", "priority": True}]),
        "strategies": json.dumps(["s"]),
        "resources": json.dumps(["r"]),
        "time_planning": json.dumps([{"goal": "a", "time": "00:30"}]),
        "expectations": json.dumps([{"goal": "a", "indicator": "i"}]),
    }
    client.post(reverse("student_entry_create"), data)
    assert SRLEntry.objects.filter(student=student).count() == 1
    client.post(reverse("student_entry_create"), data)
    assert SRLEntry.objects.filter(student=student).count() == 1
