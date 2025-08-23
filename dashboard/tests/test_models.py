import pytest
from django.contrib.auth.models import User
from dashboard.models import Classroom, Student, AppSettings


@pytest.mark.django_db
def test_classroom_str():
    teacher = User.objects.create(username="t1")
    classroom = Classroom.objects.create(teacher=teacher, name="Klasse A", group_type="CONTROL")
    assert str(classroom) == "Klasse A"


@pytest.mark.django_db
def test_student_unique_pseudonym():
    teacher = User.objects.create(username="t1")
    classroom = Classroom.objects.create(teacher=teacher, name="Klasse A", group_type="CONTROL")
    Student.objects.create(classroom=classroom, pseudonym="S1")
    with pytest.raises(Exception):
        Student.objects.create(classroom=classroom, pseudonym="S1")


@pytest.mark.django_db
def test_classroom_entry_limits_defaults():
    teacher = User.objects.create(username="t1")
    classroom = Classroom.objects.create(
        teacher=teacher, name="Klasse A", group_type="CONTROL"
    )
    assert classroom.max_entries_per_day == 1
    assert classroom.max_entries_per_week == 1


@pytest.mark.django_db
def test_appsettings_default_openai_model():
    settings = AppSettings.load()
    assert settings.openai_model == "gpt-4o-mini"
