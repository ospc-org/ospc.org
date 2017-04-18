from django import template

register = template.Library()


ACRONYMS = ["FICA"]


@register.filter
def title_with_acronym(string):
    pre = string.split(' ')
    post = []
    for x in pre:
        if x.upper() in ACRONYMS:
            post.append(x.upper())
        else:
            post.append(x.title())
    final = " ".join(post)
    return final


@register.filter
def make_id(name):
    return "-".join(name.split())


@register.filter
def block_param_title(dict):
    return dict.keys()[0].title()


@register.filter
def block_param_id(dict):
    return "-".join(dict.keys()[0].split())
