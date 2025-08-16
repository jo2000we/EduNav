import csv
import io

import openai
from openai import OpenAIError
from django import forms
from django.urls import reverse_lazy

from accounts.models import User
from config.models import SiteSettings
from lessons.models import Classroom


class SiteSettingsForm(forms.ModelForm):
    allow_ai = forms.BooleanField(required=False)
    class Meta:
        model = SiteSettings
        fields = ["openai_api_key", "allow_ai"]
        widgets = {
            "openai_api_key": forms.TextInput(
                attrs={
                    "hx-post": reverse_lazy("teacher_portal:check_openai_key"),
                    "hx-trigger": "change",
                    "hx-target": "closest div",
                    "hx-swap": "none",
                }
            ),
        }

    def clean_openai_api_key(self):
        key = self.cleaned_data.get("openai_api_key")
        if not key:
            return key
        try:
            openai.OpenAI(api_key=key).models.list()
        except OpenAIError as exc:
            raise forms.ValidationError("Invalid OpenAI API key") from exc
        return key


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["name", "use_ai"]


class StudentForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["pseudonym", "gruppe"]


class BulkStudentsForm(forms.Form):
    gruppe = forms.ChoiceField(choices=User.GROUP_CHOICES)
    pseudonyms = forms.CharField(
        widget=forms.Textarea,
        required=False,
        help_text="One pseudonym per line.",
    )
    csv_file = forms.FileField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        pseudonyms_text = cleaned_data.get("pseudonyms", "")
        csv_file = cleaned_data.get("csv_file")
        pseudonym_list: list[str] = []

        if pseudonyms_text:
            pseudonym_list.extend(
                [p.strip() for p in pseudonyms_text.splitlines() if p.strip()]
            )

        if csv_file:
            try:
                data = csv_file.read().decode("utf-8")
            except AttributeError:
                data = csv_file.read().decode()
            reader = csv.reader(io.StringIO(data))
            for row in reader:
                for field in row:
                    if field.strip():
                        pseudonym_list.append(field.strip())

        if not pseudonym_list:
            raise forms.ValidationError(
                "Please provide pseudonyms via textarea or CSV file."
            )

        cleaned_data["pseudonym_list"] = pseudonym_list
        return cleaned_data
