import pytest
from django.contrib.auth.models import User
from dashboard.models import Classroom, Student


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
