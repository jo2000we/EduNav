from django import forms
from .models import Classroom, Student, LearningGoal


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["name", "group_type"]


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["pseudonym"]


class LearningGoalForm(forms.ModelForm):
    class Meta:
        model = LearningGoal
        fields = ["text", "session_date", "achieved"]
