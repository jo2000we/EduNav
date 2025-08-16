from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name="add_attrs")
def add_attrs(field, attrs):
    """Add arbitrary attributes to a form field's widget.

    Updates ``field.field.widget.attrs`` in place so that subsequent filters
    (e.g. :func:`add_class`) operate on the augmented attribute set.
    """
    field.field.widget.attrs.update(attrs)
    return mark_safe(field.as_widget())

@register.filter(name="add_class")
def add_class(field, css):
    """Append a CSS class to the field's widget.

    The class is appended directly onto ``field.field.widget.attrs['class']``
    to avoid clobbering previously added attributes (such as HTMX attrs).
    """
    existing_classes = field.field.widget.attrs.get("class", "")
    field.field.widget.attrs["class"] = (existing_classes + " " + css).strip()
    return field.as_widget()
