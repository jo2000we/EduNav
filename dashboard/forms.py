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


import json


class PlanningForm(forms.ModelForm):
    goals = forms.CharField(widget=forms.HiddenInput())
    priorities = forms.CharField(widget=forms.HiddenInput())
    strategies = forms.CharField(widget=forms.HiddenInput())
    resources = forms.CharField(widget=forms.HiddenInput())
    time_planning = forms.CharField(widget=forms.HiddenInput())
    expectations = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = SRLEntry
        fields = [
            "goals",
            "priorities",
            "strategies",
            "resources",
            "time_planning",
            "expectations",
        ]

    def clean_goals(self):
        data = self.cleaned_data.get("goals", "[]")
        try:
            goals = json.loads(data) if data else []
        except json.JSONDecodeError:
            goals = []
        if not goals:
            raise forms.ValidationError("Mindestens ein Ziel ist erforderlich.")
        return goals

    def clean_priorities(self):
        data = self.cleaned_data.get("priorities", "[]")
        try:
            priorities = json.loads(data) if data else []
        except json.JSONDecodeError:
            priorities = []
        if not any(p.get("priority") for p in priorities):
            raise forms.ValidationError(
                "Mindestens ein Ziel muss als Priorität markiert werden."
            )
        return priorities

    def clean_strategies(self):
        data = self.cleaned_data.get("strategies", "[]")
        try:
            strategies = json.loads(data) if data else []
        except json.JSONDecodeError:
            strategies = []
        if not strategies:
            raise forms.ValidationError("Mindestens eine Strategie ist erforderlich.")
        return strategies

    def clean_resources(self):
        data = self.cleaned_data.get("resources", "[]")
        try:
            resources = json.loads(data) if data else []
        except json.JSONDecodeError:
            resources = []
        if not resources:
            raise forms.ValidationError("Mindestens eine Ressource ist erforderlich.")
        return resources

    def clean_time_planning(self):
        data = self.cleaned_data.get("time_planning", "[]")
        try:
            planning = json.loads(data) if data else []
        except json.JSONDecodeError:
            planning = []
        for item in planning:
            if item.get("time") in ("", None, "00:00"):
                raise forms.ValidationError(
                    "Für jedes Ziel muss eine Zeit größer 00:00 angegeben werden."
                )
        return planning

    def clean_expectations(self):
        data = self.cleaned_data.get("expectations", "[]")
        try:
            expectations = json.loads(data) if data else []
        except json.JSONDecodeError:
            expectations = []
        for item in expectations:
            if not item.get("indicator"):
                raise forms.ValidationError(
                    "Für jedes Ziel muss ein Indikator angegeben werden."
                )
        return expectations


class ExecutionForm(forms.ModelForm):
    steps = forms.CharField(widget=forms.HiddenInput())
    time_usage = forms.CharField(widget=forms.HiddenInput())
    strategy_check = forms.CharField(widget=forms.HiddenInput())
    problems = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "rows": 2,
            }
        ),
        label="Gab es Hindernisse? Habe ich meinen Plan angepasst – wenn ja, wie?",
    )
    emotions = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "rows": 2,
            }
        ),
        label="Wie habe ich mich gefühlt (z. B. motiviert, blockiert, zufrieden)? Was hat meine Konzentration unterstützt / gestört?",
    )

    class Meta:
        model = SRLEntry
        fields = ["steps", "time_usage", "strategy_check", "problems", "emotions"]

    def clean_steps(self):
        data = self.cleaned_data.get("steps", "[]")
        try:
            steps = json.loads(data) if data else []
        except json.JSONDecodeError:
            steps = []
        return steps

    def clean_time_usage(self):
        data = self.cleaned_data.get("time_usage", "[]")
        try:
            usage = json.loads(data) if data else []
        except json.JSONDecodeError:
            usage = []
        for item in usage:
            if item.get("time") in ("", None, "00:00"):
                raise forms.ValidationError(
                    "Für jede Beschäftigung muss eine Zeit größer 00:00 angegeben werden."
                )
        return usage

    def clean_strategy_check(self):
        data = self.cleaned_data.get("strategy_check", "[]")
        try:
            strategy = json.loads(data) if data else []
        except json.JSONDecodeError:
            strategy = []
        for item in strategy:
            if not item.get("reason"):
                raise forms.ValidationError(
                    "Für jede Strategie muss eine Begründung angegeben werden."
                )
        return strategy


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
