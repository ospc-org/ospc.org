from django import template

register = template.Library()

@register.filter
def make_id(name):
    return "-".join(name.split())


@register.filter
def make_title(name):
    return name.title()
