from __future__ import print_function
from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from pyparsing import ParseException
import six
import json

from ..constants import START_YEAR

from .models import TaxSaveInputs
from .helpers import (TaxCalcField, TaxCalcParam, default_policy, is_number,
                      int_to_nth, is_string, string_to_float_array, check_wildcards,
                      default_taxcalc_data, expand_list, propagate_user_list,
                      convert_val, INPUT, INPUTS_META)
import taxcalc


def bool_like(x):
    b = True if x == 'True' or x == True else False
    return b

def parameter_name(param):
    if not param.startswith("_"):
        param = "_" + param

    is_multi_param = any(param.endswith("_" + suffix) for suffix in ("0", "1", "2", "3"))
    if is_multi_param:
        return param[:-2]
    else:
        return param

def expand_unless_empty(param_values, param_name, param_column_name, form, new_len):
    ''' Take a list of parameters and, unless the list is empty, fill in any
    wildcards and/or expand the list to the desired number of years, using
    the proper inflation rates if necessary

    If the list is empty, return it.

    param_values: list of current values
    param_name: name of the parameter
    param_column_name: eg. _II_brk2_1 (names the sub-field)
    form: The form object that has some data for the calculation
    new_len: the new desired length of the return list

    Returns: list of length new_len, unless the empty list is passed
    '''

    if param_values == []:
        return param_values

    has_wildcards = check_wildcards(param_values)
    if len(param_values) < new_len or has_wildcards:
        #Only process wildcards and floats from this point on
        param_values = [convert_val(x) for x in param_values]
        # Discover the CPI setting for this parameter
        cpi_flag = form.discover_cpi_flag(param_name, form.cleaned_data)

        default_data = form._default_taxcalc_data[param_name]
        expnded_defaults = expand_list(default_data, new_len)

        is_multi_param = any(param_column_name.endswith("_" + suffix) for suffix in ("0", "1", "2", "3"))
        if is_multi_param:
            idx = int(param_column_name[-1])
        else:
            idx = -1

        param_values = propagate_user_list(param_values,
                                            name=param_name,
                                            defaults=expnded_defaults,
                                            cpi=cpi_flag,
                                            first_budget_year=form._first_year,
                                            multi_param_idx=idx)

        param_values = [float(x) for x in param_values]

    return param_values



class PolicyBrainForm:

    def add_fields(self, args):
        if not args:
            return args
        parsed_data = {}
        args_data = args[0]
        raw_fields = {}
        for k, v in args_data.items():
            if k not in INPUTS_META:
                raw_fields[k] = v
            elif k is 'first_year':
                parsed_data[k] = v
            else:
                pass
        parsed_data["raw_input_fields"] = json.dumps(raw_fields)
        parsed_data["input_fields"] = json.dumps("")
        return (parsed_data,)

    def add_errors_on_extra_inputs(self):
        ALLOWED_EXTRAS = {'has_errors', 'start_year', 'csrfmiddlewaretoken',
                          'data_source'}
        all_inputs = set(self.data.keys())
        allowed_inputs= set(self.fields.keys())
        extra_inputs = all_inputs - allowed_inputs - ALLOWED_EXTRAS
        for _input in extra_inputs:
            self.add_error(None, "Extra input '{0}' not allowed".format(_input))

    def do_taxcalc_validations(self):
        """
        Do minimal type checking to make sure that we did not get any
        malicious input
        """
        fields = self.cleaned_data['raw_input_fields']
        for param_name, value in fields.iteritems():
            # make sure the text parses OK
            if param_name == 'data_source':
                assert value in ('CPS', 'PUF')
            elif isinstance(value, six.string_types) and len(value) > 0:
                try:
                    INPUT.parseString(value)
                except (ParseException, AssertionError):
                    # Parse Error - we don't recognize what they gave us
                    self.add_error(param_name, "Unrecognized value: {}".format(value))
                try:
                    # reverse character is not at the beginning
                    assert value.find('<') <= 0
                except AssertionError:
                    self.add_error(
                        param_name,
                        ("Operator '<' can only be used "
                         "at the beginning")
                    )
            else:
                assert isinstance(value, bool) or len(value) == 0

    @staticmethod
    def set_form(defaults):
        """
        Setup all of the form fields and widgets with the the 2016 default data
        """
        widgets = {}
        labels = {}
        update_fields = {}
        boolean_fields = []

        for param in defaults.values():
            for field in param.col_fields:
                attrs = {
                    'class': 'form-control',
                    'placeholder': field.default_value,
                }

                if param.coming_soon:
                    attrs['disabled'] = True

                if param.tc_id in boolean_fields:
                    checkbox = forms.CheckboxInput(attrs=attrs, check_test=bool_like)
                    widgets[field.id] = checkbox
                    update_fields[field.id] = forms.BooleanField(
                        label='',
                        widget=widgets[field.id],
                        required=False
                    )
                else:
                    widgets[field.id] = forms.TextInput(attrs=attrs)
                    update_fields[field.id] = forms.fields.CharField(
                        label='',
                        widget=widgets[field.id],
                        required=False
                    )

                labels[field.id] = field.label

            if getattr(param, "inflatable", False):
                field = param.cpi_field
                attrs = {
                    'class': 'form-control sr-only',
                    'placeholder': bool(field.default_value),
                }

                if param.coming_soon:
                    attrs['disabled'] = True

                widgets[field.id] = forms.NullBooleanSelect(attrs=attrs)
                update_fields[field.id] = forms.NullBooleanField(
                    label='',
                    widget=widgets[field.id],
                    required=False
                )
        return widgets, labels, update_fields


TAXCALC_DEFAULTS = {int(START_YEAR): default_policy(int(START_YEAR))}


class TaxBrainForm(PolicyBrainForm, ModelForm):

    def __init__(self, first_year, *args, **kwargs):
        if first_year is None:
            first_year = START_YEAR
        self._first_year = int(first_year)

        # reset form data; form data from the `Meta` class is not updated each
        # time a new `TaxBrainForm` instance is created
        self.set_form_data(self._first_year)
        # move parameter fields into `raw_fields` JSON object
        args = self.add_fields(args)
        # Override `initial` with `instance`. The only relevant field
        # in `instance` is `raw_input_fields` which contains all of the user
        # input data from the stored run. By overriding the `initial` kw
        # argument we are making all of the user input from the previous run
        # as stored in the `raw_input_fields` field of `instance` available
        # to the fields attribute in django forms. This front-end data is
        # derived from this fields attribute.
        # Take a look at the source code for more info:
        # https://github.com/django/django/blob/1.9/django/forms/models.py#L284-L285
        if "instance" in kwargs:
            kwargs["initial"] = kwargs["instance"].raw_input_fields

        # Update CPI flags if either
        # 1. initial is specified in `kwargs` (reform has warning/error msgs)
        # 2. if `instance` is specified and `initial` is added above
        #    (edit parameters page)
        if kwargs.get("initial", False):
            for k, v in kwargs["initial"].iteritems():
                if k.endswith("cpi") and v:
                    # raw data is stored as choices 1, 2, 3 with the following
                    # mapping:
                    #     '1': unknown
                    #     '2': True
                    #     '3': False
                    # value_from_datadict unpacks this data:
                    # https://github.com/django/django/blob/1.9/django/forms/widgets.py#L582-L589
                    if v == '1':
                        continue
                    django_val = self.widgets[k].value_from_datadict(
                        kwargs["initial"],
                        None,
                        k
                    )
                    self.widgets[k].attrs["placeholder"] = django_val

        super(TaxBrainForm, self).__init__(*args, **kwargs)

        # update fields in a similar way as
        # https://www.pydanny.com/overloading-form-fields.html
        self.fields.update(self.update_fields.copy())

    def clean(self):
        """
        " This method should be used to provide custom model validation, and to
        modify attributes on your model if desired. For instance, you could use
        it to automatically provide a value for a field, or to do validation
        that requires access to more than a single field."
        per https://docs.djangoproject.com/en/1.8/ref/models/instances/

        Note that this can be defined both on forms and on the model, but is
        only automatically called on form submissions.
        """
        self.do_taxcalc_validations()
        self.add_errors_on_extra_inputs()

    def add_error(self, field, error):
        """
        Safely adds errors. There was an issue where the `cleaned_data`
        attribute wasn't created after `is_valid` was called. This ensures
        that the `cleaned_data` attribute is there.
        """
        if getattr(self, "cleaned_data", None) is None or self.cleaned_data is None:
            self.cleaned_data = {}
        ModelForm.add_error(self, field, error)

    def set_form_data(self, start_year):
        if start_year not in TAXCALC_DEFAULTS:
            TAXCALC_DEFAULTS[start_year] = default_policy(start_year)
        defaults = TAXCALC_DEFAULTS[start_year]
        (self.widgets, self.labels,
            self.update_fields) = PolicyBrainForm.set_form(defaults)

    class Meta:
        model = TaxSaveInputs
        # we are only updating the "first_year", "raw_fields", and "fields"
        # fields
        fields = ['first_year', 'data_source', 'raw_input_fields',
                  'input_fields']
        start_year = int(START_YEAR)
        if start_year not in TAXCALC_DEFAULTS:
            TAXCALC_DEFAULTS[start_year] = default_policy(start_year)
        (widgets, labels,
            update_fields) = PolicyBrainForm.set_form(
            TAXCALC_DEFAULTS[start_year]
        )

def has_field_errors(form, include_parse_errors=False):
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
            if include_parse_errors:
                if "Unrecognized value" in field.errors[0]:
                    return True
                else:
                    continue
            else:
                if "Unrecognized value" in field.errors[0]:
                    continue
                else:
                    return True

    return False
