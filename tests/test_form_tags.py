from django import forms
from django.test import SimpleTestCase
from django.utils.safestring import SafeString
import django

django.setup()

from config.templatetags.form_tags import add_attrs, add_class


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


class CombinedFiltersTests(SimpleTestCase):
    def test_add_attrs_then_add_class_preserves_htmx_and_class(self):
        class SampleForm(forms.Form):
            name = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Existing"}))

        form = SampleForm()
        field = form["name"]

        add_attrs(field, {"hx-post": "/post", "hx-trigger": "keyup"})
        rendered = add_class(field, "btn")

        self.assertIn('placeholder="Existing"', rendered)
        self.assertIn('hx-post="/post"', rendered)
        self.assertIn('hx-trigger="keyup"', rendered)
        self.assertIn('class="btn"', rendered)
