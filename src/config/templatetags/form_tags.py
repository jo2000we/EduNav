from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name="add_attrs")
def add_attrs(field, attrs):
    return mark_safe(field.as_widget(attrs={**field.field.widget.attrs, **attrs}))

@register.filter(name="add_class")
def add_class(field, css):
    return field.as_widget(attrs={"class": (field.field.widget.attrs.get("class", "") + " " + css).strip()})
