from django import template
import math
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template.defaultfilters import floatformat
from django.utils.safestring import mark_safe

SCALES = [
    None,
    'Thousands',
    'Millions',
    'Billions',
    'Trillions'
]


register = template.Library()


@register.filter
def scales_of_units(divisor, unit):
    scale_key = math.trunc(math.log(divisor, 1000))
    scale = SCALES[scale_key]

    if scale:
        if unit:
            return '{0} of {1}'.format(scale, unit)
        else:
            return '{0}'.format(scale)
    else:
        if unit:
            return '{0}'.format(unit)


@register.filter
def divide(value, divisor):
    try:
        return float(value) / divisor
    except ValueError:
        return 0


@register.filter
def divide_all(values, divisor):
    new_values = {}
    for value in values:
        new_values[value] = divide(values[value], divisor)
    return new_values


@register.filter
def intcomma_all(values):
    new_values = {}
    for value in values:
        new_values[value] = intcomma(values[value])
    return new_values


@register.filter
def floatformat_all(values, decimals):
    new_values = {}
    for value in values:
        new_values[value] = floatformat(values[value], decimals)
    return new_values


@register.filter()
def nbsp(value):
    return mark_safe("&nbsp;".join(value.split(' ')))
