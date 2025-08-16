from django import template

register = template.Library()

@register.filter
def add_id(field, new_id):
    """Render a form field with a different HTML id attribute."""
    return field.as_widget(attrs={"id": new_id})
