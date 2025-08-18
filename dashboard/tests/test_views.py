import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from dashboard.models import Classroom, Student


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
    classroom = Classroom.objects.create(teacher=user, name="Klasse A", group_type="CONTROL")
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
