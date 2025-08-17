from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def add_id(field, new_id):
    """Render a form field with a different HTML id attribute."""
    return field.as_widget(attrs={"id": new_id})


@register.filter
def format_priorities(priorities):
    """Format a list of priority dicts into an arrow separated string.

    Each item is expected to be a dict with ``goal`` and ``priority`` keys.
    Goals marked with ``priority=True`` are underlined to highlight them.
    """
    if not priorities:
        return ""

    parts = []
    for item in priorities:
        goal = item.get("goal", "")
        if item.get("priority"):
            goal = f"<span class='underline'>{goal}</span>"
        parts.append(goal)

    # Use a right arrow between goals.
    return mark_safe(" \u2192 ".join(parts))
