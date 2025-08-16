from django import forms
from .models import Classroom, Student, LearningGoal, SRLEntry


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


class StudentLoginForm(forms.Form):
    pseudonym = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "placeholder": "Pseudonym",
            }
        )
    )


class OverallGoalForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["overall_goal"]
        widgets = {
            "overall_goal": forms.Textarea(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "rows": 3,
                }
            )
        }


class PlanningForm(forms.ModelForm):
    class Meta:
        model = SRLEntry
        fields = [
            "session_date",
            "goal",
            "priorities",
            "strategies",
            "resources",
            "time_planning",
            "expectations",
        ]
        widgets = {
            "session_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                }
            ),
            "goal": forms.Textarea(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "rows": 3,
                }
            ),
            "priorities": forms.Textarea(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "rows": 2,
                }
            ),
            "strategies": forms.Textarea(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "rows": 2,
                }
            ),
            "resources": forms.Textarea(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "rows": 2,
                }
            ),
            "time_planning": forms.Textarea(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "rows": 2,
                }
            ),
            "expectations": forms.Textarea(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "rows": 2,
                }
            ),
        }


class ExecutionForm(forms.ModelForm):
    class Meta:
        model = SRLEntry
        fields = ["steps", "time_usage", "strategy_check", "problems", "emotions"]
        widgets = {
            field: forms.Textarea(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "rows": 2,
                }
            )
            for field in ["steps", "time_usage", "strategy_check", "problems", "emotions"]
        }


class ReflectionForm(forms.ModelForm):
    class Meta:
        model = SRLEntry
        fields = [
            "goal_achievement",
            "strategy_evaluation",
            "self_assessment",
            "time_management_reflection",
            "emotions_reflection",
            "outlook",
        ]
        widgets = {
            field: forms.Textarea(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "rows": 2,
                }
            )
            for field in [
                "goal_achievement",
                "strategy_evaluation",
                "self_assessment",
                "time_management_reflection",
                "emotions_reflection",
                "outlook",
            ]
        }
