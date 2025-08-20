import json
import pytest
import requests
from django.urls import reverse
from django.contrib.auth.models import User
from dashboard.models import Classroom, Student, SRLEntry, AppSettings


@pytest.mark.django_db
def test_classroom_list_requires_login(client):
    response = client.get(reverse("classroom_list"))
    assert response.status_code == 302  # Redirect to login


@pytest.mark.django_db
def test_classroom_list_shows_user_classrooms(client):
    user = User.objects.create_user(username="t1", password="pass")
    client.login(username="t1", password="pass")
    Classroom.objects.create(teacher=user, name="Klasse A", group_type="CONTROL")
    response = client.get(reverse("classroom_list"))
    assert b"Klasse A" in response.content


@pytest.mark.django_db
def test_settings_requires_login(client):
    response = client.get(reverse("settings"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_settings_accessible_for_teacher(client):
    user = User.objects.create_user(username="t1", password="pass")
    client.login(username="t1", password="pass")
    response = client.get(reverse("settings"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_set_class_overall_goal_updates_students(client):
    user = User.objects.create_user(username="t1", password="pass")
    client.login(username="t1", password="pass")
    classroom = Classroom.objects.create(
        teacher=user, name="Klasse A", group_type="CONTROL"
    )
    s1 = Student.objects.create(classroom=classroom, pseudonym="S1")
    s2 = Student.objects.create(classroom=classroom, pseudonym="S2")
    response = client.post(
        reverse("class_overall_goal", args=[classroom.id]),
        {"overall_goal": "Test", "overall_goal_due_date": "2024-12-31"},
    )
    assert response.status_code == 302
    s1.refresh_from_db()
    s2.refresh_from_db()
    assert s1.overall_goal == "Test"
    assert s2.overall_goal == "Test"
    assert str(s1.overall_goal_due_date) == "2024-12-31"
    assert str(s2.overall_goal_due_date) == "2024-12-31"


@pytest.mark.django_db
def test_set_class_overall_goal_prefills_form(client):
    user = User.objects.create_user(username="t1", password="pass")
    client.login(username="t1", password="pass")
    classroom = Classroom.objects.create(
        teacher=user, name="Klasse A", group_type="CONTROL"
    )
    Student.objects.create(
        classroom=classroom,
        pseudonym="S1",
        overall_goal="Bestehen",
        overall_goal_due_date="2024-12-31",
    )
    response = client.get(
        reverse("class_overall_goal", args=[classroom.id]),
        HTTP_HX_REQUEST="true",
    )
    assert b"Bestehen" in response.content
    assert b"2024-12-31" in response.content


@pytest.mark.django_db
def test_class_entry_limits_updates_classroom(client):
    user = User.objects.create_user(username="t1", password="pass")
    client.login(username="t1", password="pass")
    classroom = Classroom.objects.create(
        teacher=user,
        name="Klasse A",
        group_type="CONTROL",
        max_entries_per_day=1,
        max_entries_per_week=2,
        max_planning_execution_minutes=90,
    )
    response = client.post(
        reverse("class_entry_limits", args=[classroom.id]),
        {
            "max_entries_per_day": 3,
            "max_entries_per_week": 4,
        },
    )
    assert response.status_code == 302
    classroom.refresh_from_db()
    assert classroom.max_entries_per_day == 3
    assert classroom.max_entries_per_week == 4
    assert classroom.max_planning_execution_minutes == 90


@pytest.mark.django_db
def test_class_entry_limits_prefills_form(client):
    user = User.objects.create_user(username="t1", password="pass")
    client.login(username="t1", password="pass")
    classroom = Classroom.objects.create(
        teacher=user,
        name="Klasse A",
        group_type="CONTROL",
        max_entries_per_day=5,
        max_entries_per_week=6,
        max_planning_execution_minutes=70,
    )
    response = client.get(
        reverse("class_entry_limits", args=[classroom.id]),
        HTTP_HX_REQUEST="true",
    )
    assert b'value="5" selected' in response.content
    assert b'value="6" selected' in response.content


@pytest.mark.django_db
def test_class_time_limit_updates_classroom(client):
    user = User.objects.create_user(username="t1", password="pass")
    client.login(username="t1", password="pass")
    classroom = Classroom.objects.create(
        teacher=user,
        name="Klasse A",
        group_type="CONTROL",
        max_planning_execution_minutes=90,
    )
    response = client.post(
        reverse("class_time_limit", args=[classroom.id]),
        {
            "max_planning_execution_minutes": 80,
        },
    )
    assert response.status_code == 302
    classroom.refresh_from_db()
    assert classroom.max_planning_execution_minutes == 80


@pytest.mark.django_db
def test_class_time_limit_prefills_form(client):
    user = User.objects.create_user(username="t1", password="pass")
    client.login(username="t1", password="pass")
    classroom = Classroom.objects.create(
        teacher=user,
        name="Klasse A",
        group_type="CONTROL",
        max_planning_execution_minutes=70,
    )
    response = client.get(
        reverse("class_time_limit", args=[classroom.id]),
        HTTP_HX_REQUEST="true",
    )
    assert b'value="70"' in response.content


@pytest.mark.django_db
def test_execution_time_usage_only_checked(client):
    teacher = User.objects.create_user(username="t1", password="pass")
    classroom = Classroom.objects.create(
        teacher=teacher,
        name="Klasse A",
        group_type="CONTROL",
        max_planning_execution_minutes=90,
    )
    student = Student.objects.create(classroom=classroom, pseudonym="S1")
    entry = SRLEntry.objects.create(
        student=student,
        time_planning=[
            {"goal": "Ziel 1", "time": "00:15"},
            {"goal": "Ziel 2", "time": "00:35"},
            {"goal": "Ziel 3", "time": "00:30"},
        ],
    )
    session = client.session
    session["student_id"] = student.id
    session.save()

    usage = [
        {"goal": "Ziel 1", "time": "00:15"},
        {"goal": "Ziel 2", "time": "00:35"},
        {"goal": "Ziel 3", "time": "00:30"},
    ]
    response = client.post(
        reverse("student_entry_execution", args=[entry.id]),
        {
            "steps": json.dumps([u["goal"] for u in usage]),
            "time_usage": json.dumps(usage),
            "strategy_check": "[]",
            "problems": "",
            "emotions": "",
        },
        follow=True,
    )
    entry.refresh_from_db()
    assert response.status_code == 200
    assert entry.time_usage == usage


@pytest.mark.django_db
def test_reflection_feedback_no_entries_returns_404(client):
    teacher = User.objects.create_user(username="t1", password="pass")
    classroom = Classroom.objects.create(
        teacher=teacher,
        name="Klasse A",
        group_type="CONTROL",
    )
    student = Student.objects.create(classroom=classroom, pseudonym="S1")
    session = client.session
    session["student_id"] = student.id
    session.save()

    response = client.post(
        reverse("reflection_feedback"),
        data=json.dumps({"reflection": {}}),
        content_type="application/json",
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_reflection_feedback_uses_latest_entry(client, monkeypatch):
    teacher = User.objects.create_user(username="t1", password="pass")
    classroom = Classroom.objects.create(
        teacher=teacher,
        name="Klasse A",
        group_type="CONTROL",
    )
    student = Student.objects.create(classroom=classroom, pseudonym="S1")
    SRLEntry.objects.create(student=student)
    settings = AppSettings.load()
    settings.openai_api_key = "test"
    settings.save()

    def fake_post(url, headers=None, json=None, timeout=None):
        class Resp:
            def json(self):
                return {"choices": [{"message": {"content": "ok"}}]}

            def raise_for_status(self):
                pass

        return Resp()

    monkeypatch.setattr(requests, "post", fake_post)
    session = client.session
    session["student_id"] = student.id
    session.save()

    response = client.post(
        reverse("reflection_feedback"),
        data=json.dumps({"reflection": {}}),
        content_type="application/json",
    )
    assert response.status_code == 200
