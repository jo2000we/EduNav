import json

import pytest
from django.urls import reverse
from django.contrib.auth.models import User

from dashboard.models import Classroom, Student, SRLEntry


@pytest.mark.django_db
def test_student_detail_shows_entries(client):
    user = User.objects.create_user(username="t1", password="pass")
    classroom = Classroom.objects.create(teacher=user, name="Klasse A", group_type="CONTROL")
    student = Student.objects.create(classroom=classroom, pseudonym="S1")
    SRLEntry.objects.create(student=student, goals=["Testziel"])
    client.login(username="t1", password="pass")
    response = client.get(reverse("student_detail", args=[classroom.id, student.id]))
    assert response.status_code == 200
    assert b"Testziel" in response.content


@pytest.mark.django_db
def test_student_export_json(client):
    user = User.objects.create_user(username="t1", password="pass")
    classroom = Classroom.objects.create(teacher=user, name="Klasse A", group_type="EXPERIMENTAL")
    student = Student.objects.create(classroom=classroom, pseudonym="S1")
    SRLEntry.objects.create(student=student, session_date="2024-01-01", goals=["Z1"])
    client.login(username="t1", password="pass")
    url = reverse("student_export", args=[classroom.id, student.id])
    response = client.get(url + "?format=json")
    assert response.status_code == 200
    data = json.loads(response.content.decode("utf-8"))
    assert data["Pseudonym"] == "S1"
    assert data["Gruppenzugehörigkeit"] == "Experimentalgruppe"
    assert data["Einträge"][0]["Planung"]["Ziele"] == ["Z1"]


@pytest.mark.django_db
def test_student_export_csv(client):
    user = User.objects.create_user(username="t1", password="pass")
    classroom = Classroom.objects.create(teacher=user, name="Klasse A", group_type="CONTROL")
    student = Student.objects.create(classroom=classroom, pseudonym="S1")
    SRLEntry.objects.create(student=student, session_date="2024-01-01", goals=["Z1"])
    client.login(username="t1", password="pass")
    url = reverse("student_export", args=[classroom.id, student.id])
    response = client.get(url + "?format=csv")
    assert response.status_code == 200
    assert "text/csv" in response["Content-Type"]
    assert "Z1" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_student_export_xlsx(client):
    user = User.objects.create_user(username="t1", password="pass")
    classroom = Classroom.objects.create(teacher=user, name="Klasse A", group_type="CONTROL")
    student = Student.objects.create(classroom=classroom, pseudonym="S1")
    SRLEntry.objects.create(student=student, session_date="2024-01-01", goals=["Z1"])
    client.login(username="t1", password="pass")
    url = reverse("student_export", args=[classroom.id, student.id])
    response = client.get(url + "?format=xlsx")
    assert response.status_code == 200
    assert (
        response["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
