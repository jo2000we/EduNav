from django import forms
from django.test import SimpleTestCase
import django

django.setup()

from config.templatetags.form_tags import add_attrs, add_class


class AddAttrsFilterTests(SimpleTestCase):
    def test_preserves_existing_and_adds_htmx_attrs(self):
        class SampleForm(forms.Form):
            name = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Existing"}))

        form = SampleForm()
        field = form["name"]

        result = add_attrs(field, {"hx-post": "/post", "hx-target": "#id"})
        rendered = result.as_widget()

        self.assertIn('placeholder="Existing"', rendered)
        self.assertIn('hx-post="/post"', rendered)
        self.assertIn('hx-target="#id"', rendered)


class CombinedFiltersTests(SimpleTestCase):
    def test_add_attrs_then_add_class_preserves_htmx_and_class(self):
        class SampleForm(forms.Form):
            name = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Existing"}))

        form = SampleForm()
        field = form["name"]

        rendered = add_class(
            add_attrs(field, {"hx-post": "/post", "hx-trigger": "keyup"}),
            "btn",
        )

        self.assertIn('placeholder="Existing"', rendered)
        self.assertIn('hx-post="/post"', rendered)
        self.assertIn('hx-trigger="keyup"', rendered)
        self.assertIn('class="btn"', rendered)
