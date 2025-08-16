from collections.abc import Mapping
from django import template

register = template.Library()

@register.filter(name="add_attrs")
def add_attrs(field, attrs):
    """Add arbitrary attributes to a form field's widget.

    Updates ``field.field.widget.attrs`` in place so that subsequent filters
    (e.g. :func:`add_class`) operate on the augmented attribute set.
    Returns the original field so filters can be chained in templates.
    """
    if isinstance(attrs, Mapping):
        field.field.widget.attrs.update(attrs)
    return field

@register.filter(name="add_class")
def add_class(field, css):
    """Append a CSS class to the field's widget.

    The class is appended directly onto ``field.field.widget.attrs['class']``
    to avoid clobbering previously added attributes (such as HTMX attrs).
    """
    existing_classes = field.field.widget.attrs.get("class", "")
    field.field.widget.attrs["class"] = (existing_classes + " " + css).strip()
    return field.as_widget()
