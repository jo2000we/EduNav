from django import forms
from .models import Classroom, Student, LearningGoal, SRLEntry


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = [
            "name",
            "group_type",
            "max_entries_per_day",
            "max_entries_per_week",
            "max_planning_execution_minutes",
        ]
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
            "max_entries_per_day": forms.Select(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                }
            ),
            "max_entries_per_week": forms.Select(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                }
            ),
            "max_planning_execution_minutes": forms.NumberInput(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "min": 1,
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


class PseudoForm(forms.Form):
    pseudonym = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "placeholder": "Pseudonym",
            }
        )
    )


class PasswordLoginForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "placeholder": "Passwort",
            }
        )
    )


class SetPasswordForm(forms.Form):
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "placeholder": "Passwort",
            }
        )
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "placeholder": "Passwort bestätigen",
            }
        )
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwörter stimmen nicht überein.")
        return cleaned


class OverallGoalForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["overall_goal", "overall_goal_due_date"]
        widgets = {
            "overall_goal": forms.Textarea(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "rows": 3,
                }
            ),
            "overall_goal_due_date": forms.DateInput(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "type": "date",
                }
            ),
        }


class ClassOverallGoalForm(forms.Form):
    overall_goal = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "rows": 3,
            }
        )
    )
    overall_goal_due_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "type": "date",
            }
        )
    )


class ClassEntryLimitForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = [
            "max_entries_per_day",
            "max_entries_per_week",
        ]
        widgets = {
            "max_entries_per_day": forms.Select(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                }
            ),
            "max_entries_per_week": forms.Select(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                }
            ),
        }


class ClassTimeLimitForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["max_planning_execution_minutes"]
        widgets = {
            "max_planning_execution_minutes": forms.NumberInput(
                attrs={
                    "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                    "min": 1,
                }
            ),
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
        label="Gibt es Hindernisse? Passe ich meinen Plan an – wenn ja, wie?",
    )
    emotions = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "rows": 2,
            }
        ),
        label="Wie fühle ich mich (z. B. motiviert, blockiert, zufrieden)? Was unterstützt / stört meine Konzentration?",
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
        return usage

    def clean_strategy_check(self):
        data = self.cleaned_data.get("strategy_check", "[]")
        try:
            strategy = json.loads(data) if data else []
        except json.JSONDecodeError:
            strategy = []
        return strategy


class ReflectionForm(forms.ModelForm):
    goal_achievement = forms.CharField(widget=forms.HiddenInput())
    strategy_evaluation = forms.CharField(widget=forms.HiddenInput())
    learned_subject = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "rows": 2,
            }
        ),
        label="Was habe ich fachlich gelernt?",
    )
    learned_work = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "rows": 2,
            }
        ),
        label="Was habe ich über meine Arbeitsweise gelernt?",
    )
    planning_realistic = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "rows": 2,
            }
        ),
        label="War meine Planung realistisch?",
    )
    planning_deviations = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "rows": 2,
            }
        ),
        label="Wo gab es Abweichungen?",
    )
    motivation_rating = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "rows": 2,
            }
        ),
        label="Wie bewerte ich meine Motivation über die Zeit hinweg?",
    )
    motivation_improve = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "rows": 2,
            }
        ),
        label="Was könnte ich tun, um sie zu stärken?",
    )
    next_phase = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "rows": 2,
            }
        ),
        label="Was nehme ich mir für die nächste Phase konkret vor?",
    )
    strategy_outlook = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 p-2.5",
                "rows": 2,
            }
        ),
        label="Welche Strategien will ich beibehalten oder ändern?",
    )

    class Meta:
        model = SRLEntry
        fields = [
            "goal_achievement",
            "strategy_evaluation",
            "learned_subject",
            "learned_work",
            "planning_realistic",
            "planning_deviations",
            "motivation_rating",
            "motivation_improve",
            "next_phase",
            "strategy_outlook",
        ]

    def clean_goal_achievement(self):
        data = self.cleaned_data.get("goal_achievement", "[]")
        try:
            ga = json.loads(data) if data else []
        except json.JSONDecodeError:
            ga = []
        for item in ga:
            if not item.get("achievement") or not item.get("comment"):
                raise forms.ValidationError(
                    "Für jedes Ziel muss eine Einschätzung und ein Kommentar angegeben werden."
                )
        return ga

    def clean_strategy_evaluation(self):
        data = self.cleaned_data.get("strategy_evaluation", "[]")
        try:
            se = json.loads(data) if data else []
        except json.JSONDecodeError:
            se = []
        for item in se:
            if not item.get("helpful") or not item.get("reuse"):
                raise forms.ValidationError(
                    "Für jede Strategie muss angegeben werden, ob sie geholfen hat und ob sie erneut genutzt wird."
                )
        return se
