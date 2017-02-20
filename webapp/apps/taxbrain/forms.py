from __future__ import print_function
from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from pyparsing import ParseException

from .models import TaxSaveInputs
from .helpers import (TaxCalcField, TaxCalcParam, default_policy, is_number,
                      int_to_nth, is_string, string_to_float_array, check_wildcards,
                      default_taxcalc_data, expand_list, propagate_user_list,
                      convert_val, INPUT)
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



TAXCALC_DEFAULTS_2016 = default_policy(2016)


class PersonalExemptionForm(ModelForm):

    def __init__(self, first_year, *args, **kwargs):
        self._first_year = int(first_year)
        self._default_params = default_policy(self._first_year)

        self._default_meta = default_taxcalc_data(taxcalc.policy.Policy,
                               start_year=self._first_year, metadata=True)


        self._default_taxcalc_data = default_taxcalc_data(taxcalc.policy.Policy,
                                         start_year=self._first_year)
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

        super(PersonalExemptionForm, self).__init__(*args, **kwargs)

    def discover_cpi_flag(self, param, user_values):
        ''' Helper function to discover the CPI setting for this parameter'''

        cpi_flag_from_user = user_values.get(param + "_cpi", None)
        if cpi_flag_from_user is None:
            cpi_flag_from_user = user_values.get("_" + param + "_cpi", None)
        if cpi_flag_from_user is None:
            cpi_flag_from_user = user_values.get(param[1:] + "_cpi", None)

        if cpi_flag_from_user is None:
            attrs = self._default_meta[param]
            cpi_flag = attrs.get('cpi_inflated', False)
        else:
            cpi_flag = cpi_flag_from_user
        return cpi_flag

    def get_comp_data(self, comp_key, param_id, col, param_values):
        """
        Get the data necessary for a min/max validation comparison, given:
            param_id - The webapp-internal TC parameter ID
            col - The column number for the param
            comp_key - a key that is either:
               * a static value
               * the word 'default' - we should use the field's defaults
               * the name of another param - we should use that param's
                 corresponding column field. If values have been submitted for
                 it, use them. Otherwise use its defaults
             param_values - either user supplied or default values of the
                            parameter

        After finding the proper data, expand it to the required length.
        Either the parameter specified by comp_key, or the parameter referred
        by param_id may need to be extended and have wildcard entries
        replaced.

        Returns: dict
                 'source': text for error reporting
                 'comp_data': a sequence of values associated with param
                 'epx_col_values': a (possibly) expanded set of column values
                                   for comparison against comp_data
            
        """

        len_param_values = len(param_values)
        param_name = "_" + param_id
        param_column_name = param_name + "_" + str(col)

        if is_number(comp_key):
            source = "the static value"
            new_len = len_param_values
            comp_data = [comp_key]
            len_diff = len_param_values - len(comp_data)
            # No inflation of static values, just repeat
            if len_diff > 0:
                comp_data += [comp_data[-1]] * len_diff
            col_values = param_values

        elif comp_key == 'default':
            source = "this field's default"
            new_len = len_param_values
            # Grab the default values and expand if necessary
            base_param = self._default_params[param_id]
            base_col = base_param.col_fields[col]
            comp_data = base_col.values
            len_diff = len_param_values - len(comp_data)
            if len_diff > 0:
                new_data = expand_unless_empty(comp_data, param_name,
                                   param_column_name, self, new_len)
                comp_data = new_data
            col_values = param_values

        elif comp_key in self._default_params:
            # Comparing two parameters against each other, either of
            # which might be expanded and have wildcards
            other_param = self._default_params[comp_key]
            other_col = other_param.col_fields[col]
            other_values = None
            other_param_name = parameter_name(other_col.id)
            other_param_column_name = other_col.id
            new_len = len_param_values

            if other_col.id in self.cleaned_data:
                other_values_raw = self.cleaned_data[other_col.id]
                try:
                    other_values = string_to_float_array(other_values_raw)
                    new_len = max(len_param_values, len(other_values))
                    other_values = expand_unless_empty(other_values, other_param_name,
                                            other_param_column_name, self,
                                            new_len)

                except ValueError as ve:
                    # Assume wildcards here
                    other_values_list = other_values_raw.split(',')
                    new_len = max(len_param_values, len(other_values_list))
                    other_values = expand_unless_empty(other_values_list, other_param_name,
                                        other_param_column_name, self,
                                        new_len)

            if other_values:
                comp_data = other_values
                source = other_param.name + "'s value"
            else:
                other_defaults = other_col.values
                comp_data = expand_unless_empty(other_defaults, other_param_name,
                                   other_param_column_name, self, new_len)
                source = other_param.name + "'s default"
            col_values = expand_unless_empty(param_values, param_name, param_column_name, self, new_len)
        else:
            raise ValueError('Unknown comp keyword "{0}"'.format(comp_key))

        if len(comp_data) < 1:
            raise ValueError('No comparison data found for kw'.format(comp_key))

        assert len(comp_data) == len(col_values)
        return {'source': source, 'comp_data': comp_data, 'exp_col_values': col_values}

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

    def add_errors_on_extra_inputs(self):
        ALLOWED_EXTRAS = {'has_errors', 'start_year', 'csrfmiddlewaretoken'}
        all_inputs = set(self.data.keys())
        allowed_inputs= set(self.fields.keys())
        extra_inputs = all_inputs - allowed_inputs - ALLOWED_EXTRAS
        for _input in extra_inputs:
            self.add_error(None, "Extra input '{0}' not allowed".format(_input))

    def do_taxcalc_validations(self):
        """
        Run the validations specified by Taxcalc's param definitions

        Each parameter can be assigned a min and a max, the value of which can
        be statically defined or determined dynamically via a keyword.

        Keywords correlate to submitted value array for a different parameter,
        or to the default value array for the validated field.

        We could define these on individual fields instead, but we would need to
        define all the field data dynamically both here and on the model,
        and it's not yet possible on the model due to issues with how migrations
        are detected.
        """

        for param_id, param in self._default_params.iteritems():
            if param.coming_soon or param.hidden:
                continue

            # First make sure the text parses OK
            BOOLEAN_FLAGS = (u'True', u'False')
            found_parse_error = False
            for col, col_field in enumerate(param.col_fields):
                if col_field.id not in self.cleaned_data:
                    continue

                submitted_col_values_raw = self.cleaned_data[col_field.id]

                if len(submitted_col_values_raw) > 0 and submitted_col_values_raw not in BOOLEAN_FLAGS:
                    try:
                        INPUT.parseString(submitted_col_values_raw)
                    except ParseException as pe:
                        # Parse Error - we don't recognize what they gave us
                        self.add_error(col_field.id, "Unrecognized value: {}".format(submitted_col_values_raw))
                        found_parse_error = True

            if found_parse_error:
                continue

            # Move on if there is no min/max validation necessary
            if param.max is None and param.min is None:
                continue

            for col, col_field in enumerate(param.col_fields):
                submitted_col_values_raw = self.cleaned_data[col_field.id]
                try:
                    submitted_col_values = string_to_float_array(submitted_col_values_raw)
                except ValueError as ve:
                    # Assuming wildcard notation here
                    submitted_col_values_list = submitted_col_values_raw.split(',')
                    param_name = parameter_name(col_field.id)
                    submitted_col_values = expand_unless_empty(submitted_col_values_list, param_name, col_field.id, self, len(submitted_col_values_list))
                default_col_values = col_field.values

                # If we change a different field which this field relies on for
                # validation, we must ensure this is validated even if unchanged
                # from defaults
                if submitted_col_values:
                    col_values = submitted_col_values
                else:
                    col_values = default_col_values

                if param.max is not None:
                    comp = self.get_comp_data(param.max, param_id, col, col_values)
                    source = comp['source']
                    maxes = comp['comp_data']
                    exp_col_values = comp['exp_col_values']

                    for i, value in enumerate(exp_col_values):
                        if value > maxes[i]:
                            if len(col_values) == 1:
                                self.add_error(col_field.id,
                                               u"Must be \u2264 {0} of {1}".
                                               format(source, maxes[i]))
                            else:
                                self.add_error(col_field.id,
                                               u"{0} value must be \u2264 \
                                               {1}'s {0} value of {2}".format(
                                                   int_to_nth(i + 1),
                                                   source, maxes[i]))

                if param.min is not None:
                    comp = self.get_comp_data(param.min, param_id, col, col_values)
                    source = comp['source']
                    mins = comp['comp_data']
                    exp_col_values = comp['exp_col_values']

                    for i, value in enumerate(exp_col_values):
                        if value < mins[i]:
                            if len(col_values) == 1:
                                self.add_error(col_field.id,
                                               u"Must be \u2265 {0} of {1}".
                                               format(source, mins[i]))
                            else:
                                self.add_error(col_field.id,
                                               u"{0} value must be \u2265 \
                                               {1}'s {0} value of {2}".format(
                                                   int_to_nth(i + 1),
                                                   source, mins[i]))

    class Meta:
        model = TaxSaveInputs
        exclude = ['creation_date']
        widgets = {}
        labels = {}

        for param in TAXCALC_DEFAULTS_2016.values():
            for field in param.col_fields:
                attrs = {
                    'class': 'form-control',
                    'placeholder': field.default_value,
                }

                if param.coming_soon:
                    attrs['disabled'] = True

                if param.tc_id == "_ID_BenefitSurtax_Switch" or param.tc_id == "_ID_BenefitCap_Switch":
                    checkbox = forms.CheckboxInput(attrs=attrs, check_test=bool_like)
                    widgets[field.id] = checkbox
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
