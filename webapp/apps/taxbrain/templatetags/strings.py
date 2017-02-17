from django import template

register = template.Library()

@register.filter
def make_id(name):
    return "-".join(name.split())

@register.filter
def block_param_title(dict):
    return dict.keys()[0].title()

@register.filter
def block_param_id(dict):
    return "-".join(dict.keys()[0].split())
