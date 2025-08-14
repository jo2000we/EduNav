from django import forms

from config.models import SiteSettings
from lessons.models import Classroom


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ["openai_api_key", "allow_ai"]
        widgets = {
            "openai_api_key": forms.PasswordInput(render_value=True),
        }


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["name", "code", "use_ai"]
