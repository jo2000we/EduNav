import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from dashboard.models import Classroom


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
