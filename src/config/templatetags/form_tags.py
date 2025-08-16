from django import template

register = template.Library()

@register.filter(name="add_attrs")
def add_attrs(field, attrs):
    merged_attrs = field.field.widget.attrs.copy()
    merged_attrs.update(attrs)
    field.field.widget.attrs = merged_attrs
    return field

@register.filter(name="add_class")
def add_class(field, css):
    return field.as_widget(attrs={"class": (field.field.widget.attrs.get("class", "") + " " + css).strip()})
