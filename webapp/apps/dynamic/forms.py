from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from .models import DynamicSaveInputs
from ..taxbrain.helpers import (TaxCalcField, TaxCalcParam)
from .helpers import default_parameters

def bool_like(x):
    b = True if x == 'True' or x == True else False
    return b

OGUSA_DEFAULT_PARAMS = default_parameters(2015)

class DynamicInputsModelForm(ModelForm):

    class Meta:
        model = DynamicSaveInputs
        exclude = ['creation_date']
        widgets = {}
        labels = {}
        import pdb;pdb.set_trace()
        for param in OGUSA_DEFAULT_PARAMS.values():
            for field in param.col_fields:
                attrs = {
                    'class': 'form-control',
                    'placeholder': field.default_value,
                }

                if param.coming_soon:
                    attrs['disabled'] = True
                    attrs['checked'] = False
                    widgets[field.id] = forms.CheckboxInput(attrs=attrs, check_test=bool_like)
                else:
                    widgets[field.id] = forms.TextInput(attrs=attrs)

                labels[field.id] = field.label

            if param.inflatable:
                field = param.cpi_field
                attrs = {
                    'class': 'form-control sr-only',
                    'placeholder': bool(field.default_value),
                }

                if param.coming_soon:
                    attrs['disabled'] = True

                widgets[field.id] = forms.NullBooleanSelect(attrs=attrs)


def has_field_errors(form):
    """
    This allows us to see if we have field_errors, as opposed to only having
    form.non_field_errors. I would prefer to put this in a template tag, but
    getting that working with a conditional statement in a template was very
    challenging.
    """
    if not form.errors:
        return False

    for field in form:
        if field.errors:
            return True

    return False
