from django import template

register = template.Library()

@register.filter
def col_input_class(taxcalc_param):
    cols = len(taxcalc_param.col_fields)
    display_cols = 12
    display_size = min([int(display_cols / cols), 6])
    return "col-xs-{0}".format(display_size)

