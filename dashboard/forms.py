from django import forms
from .models import Classroom, Student, LearningGoal


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["name", "group_type"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "placeholder": "Klassenname",
                }
            ),
            "group_type": forms.Select(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                }
            ),
        }


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["pseudonym"]
        widgets = {
            "pseudonym": forms.TextInput(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "placeholder": "Pseudonym",
                }
            ),
        }


class LearningGoalForm(forms.ModelForm):
    class Meta:
        model = LearningGoal
        fields = ["text", "session_date", "achieved"]
