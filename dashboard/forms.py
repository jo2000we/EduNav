from django import forms
from .models import Classroom, Student, LearningGoal, DayEntry


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


class GoalForm(forms.Form):
    text = forms.CharField(
        label="Ein Ziel festlegen:",
        widget=forms.TextInput(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "placeholder": "Mein Ziel",
            }
        ),
    )


class PlanningForm(forms.ModelForm):

    class Meta:
        model = DayEntry
        fields = ["session_date", "strategies", "resources", "expectations"]
        labels = {
            "session_date": "Datum",
            "strategies": "Vorgehen/Strategien: Wie will ich vorgehen?",
            "resources": "Ressourcen: Welche Materialien, Werkzeuge, Personen brauche ich?",
            "expectations": "Erwartungen: Woran merke ich am Ende, dass ich erfolgreich war?",
        }
        widgets = {
            "session_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
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
            "expectations": forms.Textarea(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "rows": 2,
                }
            ),
        }


class ExecutionForm(forms.ModelForm):

    class Meta:
        model = DayEntry
        fields = ["steps", "strategy_check", "problems", "emotions_execution"]
        labels = {
            "steps": "Arbeitsschritte: Was habe ich konkret gemacht?",
            "strategy_check": "Strategien überprüfen: Welche Methoden habe ich eingesetzt? Waren diese zielführend?",
            "problems": "Probleme & Anpassungen: Gab es Hindernisse? Habe ich meinen Plan angepasst – wenn ja, wie?",
            "emotions_execution": "Emotionen & Motivation: Wie habe ich mich gefühlt? Was hat meine Konzentration unterstützt / gestört?",
        }
        widgets = {
            field: forms.Textarea(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "rows": 2,
                }
            )
            for field in ["steps", "strategy_check", "problems", "emotions_execution"]
        }


class ReflectionForm(forms.ModelForm):

    class Meta:
        model = DayEntry
        fields = [
            "strategy_evaluation",
            "self_assessment",
            "time_management_reflection",
            "emotions_reflection",
            "outlook",
        ]
        labels = {
            "strategy_evaluation": "Strategien bewerten: Welche Vorgehensweisen waren erfolgreich? Welche weniger hilfreich?",
            "self_assessment": "Selbsteinschätzung: Was habe ich fachlich gelernt? Was habe ich über meine Arbeitsweise gelernt?",
            "time_management_reflection": "Zeitmanagement: War meine Planung realistisch? Wo gab es Abweichungen?",
            "emotions_reflection": "Emotionen/Motivation: Wie bewerte ich meine Motivation über die Zeit hinweg? Was könnte ich tun, um sie zu stärken?",
            "outlook": "Ausblick: Was nehme ich mir für die nächste Phase konkret vor? Welche Strategien will ich beibehalten oder ändern?",
        }
        widgets = {
            field: forms.Textarea(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "rows": 2,
                }
            )
            for field in [
                "strategy_evaluation",
                "self_assessment",
                "time_management_reflection",
                "emotions_reflection",
                "outlook",
            ]
        }
