from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from .models import BTaxSaveInputs
from .helpers import (BTaxField, BTaxParam, get_btax_defaults,
                      convert_val, make_bool)
from ..taxbrain.helpers import (is_number, int_to_nth,
                                is_string, string_to_float_array,
                                check_wildcards, expand_list,
                                propagate_user_list)
import taxcalc

from ..taxbrain.forms import (has_field_errors,
                              bool_like,
                              parameter_name)

from ..constants import START_YEAR

BTAX_DEFAULTS = get_btax_defaults(START_YEAR)

class BTaxExemptionForm(ModelForm):

    def __init__(self, first_year, *args, **kwargs):
        self._first_year = int(first_year)
        self._default_params = get_btax_defaults(first_year)

        # Defaults are set in the Meta, but we need to swap
        # those outs here in the init because the user may
        # have chosen a different start year
        all_defaults = []
        for param in list(self._default_params.values()):
            for field in param.col_fields:
                all_defaults.append((field.id, field.default_value))
        for _id, default in all_defaults:
            if hasattr(self._meta.widgets[_id], 'attrs'):
                self._meta.widgets[_id].attrs['placeholder'] = default

        super(BTaxExemptionForm, self).__init__(*args, **kwargs)

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
        self.do_btax_validations()
        self.add_errors_on_extra_inputs()

    def add_errors_on_extra_inputs(self):
        ALLOWED_EXTRAS = {'has_errors', 'start_year', 'csrfmiddlewaretoken'}
        all_inputs = set(self.data.keys())
        allowed_inputs= set(self.fields.keys())
        extra_inputs = all_inputs - allowed_inputs - ALLOWED_EXTRAS
        for _input in extra_inputs:
            self.add_error(None, "Extra input '{0}' not allowed".format(_input))

    def do_btax_validations(self):
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

        for param_id, param in self._default_params.items():
            if any(token in param_id for token in ('gds', 'ads', 'tax')):
                param.col_fields[0].values[0] = make_bool(param.col_fields[0].values[0])
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
                                               "Must be \u2264 {0} of {1}".
                                               format(source, maxes[i]))
                            else:
                                self.add_error(col_field.id,
                                               "{0} value must be \u2264 \
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
                                               "Must be \u2265 {0} of {1}".
                                               format(source, mins[i]))
                            else:
                                self.add_error(col_field.id,
                                               "{0} value must be \u2265 \
                                               {1}'s {0} value of {2}".format(
                                                   int_to_nth(i + 1),
                                                   source, mins[i]))

    class Meta:
        model = BTaxSaveInputs
        exclude = ['creation_date']
        widgets = {}
        labels = {}

        for param in list(BTAX_DEFAULTS.values()):
            for field in param.col_fields:
                attrs = {
                    'class': 'form-control',
                    'placeholder': field.default_value,
                }

                if param.coming_soon:
                    attrs['disabled'] = True

                if '_Switch' in param.tc_id:
                    item = forms.CheckboxInput(attrs=attrs, check_test=bool_like)
                    widgets[field.id] = item
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
