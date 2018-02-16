from __future__ import print_function
from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from pyparsing import ParseException
import six
import json

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
        ALLOWED_EXTRAS = {'has_errors', 'start_year', 'csrfmiddlewaretoken'}
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
            if isinstance(value, six.string_types) and len(value) > 0:
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


TAXCALC_DEFAULTS_2016 = default_policy(2016)


class TaxBrainForm(PolicyBrainForm, ModelForm):

    def __init__(self, first_year, *args, **kwargs):
        # move parameter fields into `raw_fields` JSON object
        args = self.add_fields(args)
        # this seems to update the saved data in the appropriate way
        if "instance" in kwargs:
            kwargs["initial"] = kwargs["instance"].raw_input_fields
        self._first_year = int(first_year)
        self._default_params = default_policy(self._first_year)

        # Defaults are set in the Meta, but we need to swap
        # those outs here in the init because the user may
        # have chosen a different start year
        all_defaults = []
        for param in self._default_params.values():
            for field in param.col_fields:
                all_defaults.append((field.id, field.default_value))

        for _id, default in all_defaults:
            self._meta.widgets[_id].attrs['placeholder'] = default

        # If a stored instance is passed,
        # set CPI flags based on the values in this instance
        if 'instance' in kwargs:
            instance = kwargs['instance']
            cpi_flags = [attr for attr in dir(instance) if attr.endswith('_cpi')]
            for flag in cpi_flags:
                if getattr(instance, flag) is not None and flag in self._meta.widgets:
                    self._meta.widgets[flag].attrs['placeholder'] = getattr(instance, flag)

        super(TaxBrainForm, self).__init__(*args, **kwargs)
        # update fields in a similar way as
        # https://www.pydanny.com/overloading-form-fields.html
        self.fields.update(self.Meta.update_fields)

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

    class Meta:

        model = TaxSaveInputs
        # we are only updating the "first_year", "raw_fields", and "fields"
        # fields
        fields = ['first_year', 'raw_input_fields', 'input_fields']
        widgets = {}
        labels = {}
        update_fields = {}
        boolean_fields = [
            "_ID_BenefitSurtax_Switch",
            "_ID_BenefitCap_Switch",
            "_ALD_InvInc_ec_base_RyanBrady",
            "_NIIT_PT_taxed",
            "_CG_nodiff",
            "_EITC_indiv",
            "_CTC_new_refund_limited",
            "_II_no_em_nu18",
            "_ID_AmountCap_Switch",
            "_CTC_new_for_all",
            "_CTC_new_refund_limited_all_payroll",
            "_PT_wages_active_income",
            "_PT_top_stacking",
        ]

        for param in TAXCALC_DEFAULTS_2016.values():
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

            if param.inflatable:
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
