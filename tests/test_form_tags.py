from django import forms
from django.test import SimpleTestCase
from django.utils.safestring import SafeString

from config.templatetags.form_tags import add_attrs


class AddAttrsFilterTests(SimpleTestCase):
    def test_preserves_existing_and_adds_htmx_attrs(self):
        class SampleForm(forms.Form):
            name = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Existing"}))

        form = SampleForm()
        field = form["name"]

        rendered = add_attrs(field, {"hx-post": "/post", "hx-target": "#id"})

        self.assertIsInstance(rendered, SafeString)
        self.assertIn('placeholder="Existing"', rendered)
        self.assertIn('hx-post="/post"', rendered)
        self.assertIn('hx-target="#id"', rendered)
