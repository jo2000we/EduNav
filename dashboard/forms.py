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
        labels = {
            "session_date": "Datum",
            "priorities": "Prioritäten: Welche Aufgaben sind am wichtigsten?",
            "strategies": "Vorgehen/Strategien: Wie will ich vorgehen? (z. B. Recherche, Entwürfe, Austausch, Versuch & Irrtum)",
            "resources": "Ressourcen: Welche Materialien, Werkzeuge, Personen brauche ich?",
            "time_planning": "Zeitplanung: Wie lange möchte ich für welche Aufgabe arbeiten?",
            "expectations": "Erwartungen: Woran merke ich am Ende, dass ich erfolgreich war?",
        }

    def clean_priorities(self):
        data = self.cleaned_data.get("priorities", "")
        if data:
            return [line.strip() for line in data.splitlines() if line.strip()]
        return []

    def clean_time_planning(self):
        data = self.cleaned_data.get("time_planning", "")
        if data:
            return [line.strip() for line in data.splitlines() if line.strip()]
        return []


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
        labels = {
            "steps": "Was habe ich konkret gemacht?",
            "time_usage": "Wie viel Zeit habe ich tatsächlich gebraucht?",
            "strategy_check": "Welche Methoden habe ich eingesetzt? Waren diese zielführend?",
            "problems": "Gab es Hindernisse? Habe ich meinen Plan angepasst – wenn ja, wie?",
            "emotions": "Wie habe ich mich gefühlt (z. B. motiviert, blockiert, zufrieden)? Was hat meine Konzentration unterstützt / gestört?",
        }

    def clean_steps(self):
        data = self.cleaned_data.get("steps", "")
        if data:
            return [line.strip() for line in data.splitlines() if line.strip()]
        return []

    def clean_time_usage(self):
        data = self.cleaned_data.get("time_usage", "")
        if data:
            return [line.strip() for line in data.splitlines() if line.strip()]
        return []


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
        labels = {
            "goal_achievement": "Habe ich meine Ziele erreicht? (vollständig / teilweise / nicht)",
            "strategy_evaluation": "Welche Vorgehensweisen waren erfolgreich? Welche weniger hilfreich?",
            "self_assessment": "Was habe ich fachlich gelernt? Was habe ich über meine Arbeitsweise gelernt?",
            "time_management_reflection": "War meine Planung realistisch? Wo gab es Abweichungen?",
            "emotions_reflection": "Wie bewerte ich meine Motivation über die Zeit hinweg? Was könnte ich tun, um sie zu stärken?",
            "outlook": "Was nehme ich mir für die nächste Phase konkret vor? Welche Strategien will ich beibehalten oder ändern?",
        }

    def clean_goal_achievement(self):
        data = self.cleaned_data.get("goal_achievement", "")
        if data:
            return [line.strip() for line in data.splitlines() if line.strip()]
        return []
