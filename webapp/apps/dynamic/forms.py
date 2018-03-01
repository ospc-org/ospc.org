from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from .models import (DynamicSaveInputs, DynamicBehaviorSaveInputs,
                     DynamicElasticitySaveInputs)
from ..taxbrain.helpers import (TaxCalcField, TaxCalcParam,
                                string_to_float_array, int_to_nth,
                                is_string, is_number)
from ..taxbrain.forms import PolicyBrainForm
from .helpers import (default_parameters, default_behavior_parameters,
                      default_elasticity_parameters)

def bool_like(x):
    b = True if x == 'True' or x == True else False
    return b

OGUSA_DEFAULT_PARAMS = default_parameters(2015)
BEHAVIOR_DEFAULT_PARAMS = default_behavior_parameters(2015)
ELASTICITY_DEFAULT_PARAMS = default_elasticity_parameters(2015)

class DynamicElasticityInputsModelForm(ModelForm):

    def __init__(self, first_year, *args, **kwargs):
        self._first_year = int(first_year)
        self._default_params = default_elasticity_parameters(self._first_year)
        # Defaults are set in the Meta, but we need to swap
        # those outs here in the init because the user may
        # have chosen a different start year
        all_defaults = []
        for param in self._default_params.values():
            for field in param.col_fields:
                all_defaults.append((field.id, field.default_value))

        for _id, default in all_defaults:
            self._meta.widgets[_id].attrs['placeholder'] = default

        super(DynamicElasticityInputsModelForm, self).__init__(*args, **kwargs)

    def get_comp_data(self, comp_key, param_id, col, required_length):
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
             required_len - The number of values we need to compare against

        After finding the proper data, expand it to the required_length by
        repeating the final value.

        @todo: CPI inflate the final value to fill instead of simply repeating
        """

        base_param = self._default_params[param_id]
        base_col = base_param.col_fields[col]

        if is_number(comp_key):
            comp_data = [comp_key]
            source = "the static value"
        elif comp_key == 'default':
            comp_data = base_col.values
            source = "this field's default"
        elif comp_key in self._default_params:
            other_param = self._default_params[comp_key]
            other_col = other_param.col_fields[col]
            other_values = None

            if other_col.id in self.cleaned_data:
                other_values_raw = self.cleaned_data[other_col.id]
                other_values = string_to_float_array(other_values_raw)

            if other_values:
                comp_data = other_values
                source = other_param.name + "'s value"
            else:
                other_defaults = other_col.values
                comp_data = other_defaults
                source = other_param.name + "'s default"
        else:
            raise ValueError('Unknown comp keyword "{0}"'.format(comp_key))

        if len(comp_data) < 1:
            raise ValueError('No comparison data found for kw'.format(comp_key))

        len_diff = required_length - len(comp_data)
        if len_diff > 0:
            comp_data += [comp_data[-1]] * len_diff

        return {'source': source, 'comp_data': comp_data}

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

            if param.max is None and param.min is None:
                continue

            for col, col_field in enumerate(param.col_fields):
                submitted_col_values_raw = self.cleaned_data[col_field.id]
                submitted_col_values = string_to_float_array(submitted_col_values_raw)
                default_col_values = col_field.values

                # If we change a different field which this field relies on for
                # validation, we must ensure this is validated even if unchanged
                # from defaults
                if submitted_col_values:
                    col_values = submitted_col_values
                else:
                    col_values = default_col_values

                if param.max is not None:
                    comp = self.get_comp_data(param.max, param_id, col, len(col_values))
                    source = comp['source']
                    maxes = comp['comp_data']

                    for i, value in enumerate(col_values):
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
                    comp = self.get_comp_data(param.min, param_id, col, len(col_values))
                    source = comp['source']
                    mins = comp['comp_data']

                    for i, value in enumerate(col_values):
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
        model = DynamicElasticitySaveInputs
        exclude = ['creation_date']
        widgets = {}
        labels = {}
        for param in ELASTICITY_DEFAULT_PARAMS.values():
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


class DynamicBehavioralInputsModelForm(PolicyBrainForm, ModelForm):

    def __init__(self, first_year, *args, **kwargs):
        # reset form data; form data from the `Meta` class is not updated each
        # time a new `TaxBrainForm` instance is created
        self.set_form_data()
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

        if first_year is None:
            first_year = START_YEAR
        self._first_year = int(first_year)
        self._default_params = default_behavior_parameters(self._first_year)
        # Defaults are set in the Meta, but we need to swap
        # those out here in the init because the user may
        # have chosen a different start year
        all_defaults = []
        for param in self._default_params.values():
            for field in param.col_fields:
                all_defaults.append((field.id, field.default_value))

        for _id, default in all_defaults:
            self.widgets[_id].attrs['placeholder'] = default

        super(DynamicBehavioralInputsModelForm, self).__init__(*args, **kwargs)

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

    def set_form_data(self):
        (self.widgets, self.labels,
            self.update_fields) = PolicyBrainForm.set_form(BEHAVIOR_DEFAULT_PARAMS)


    class Meta:
        model = DynamicBehaviorSaveInputs
        # we are only updating the "first_year", "raw_fields", and "fields"
        # fields
        fields = ['first_year', 'raw_input_fields', 'input_fields']
        (widgets, labels,
            update_fields) = PolicyBrainForm.set_form(BEHAVIOR_DEFAULT_PARAMS)


class DynamicInputsModelForm(ModelForm):

    def __init__(self, first_year, *args, **kwargs):
        self._first_year = int(first_year)
        self._default_params = default_parameters(self._first_year)
        # Defaults are set in the Meta, but we need to swap
        # those outs here in the init because the user may
        # have chosen a different start year
        all_defaults = []
        for param in self._default_params.values():
            for field in param.col_fields:
                all_defaults.append((field.id, field.default_value))

        for _id, default in all_defaults:
            self._meta.widgets[_id].attrs['placeholder'] = default

        super(DynamicInputsModelForm, self).__init__(*args, **kwargs)

    def get_comp_data(self, comp_key, param_id, col, required_length):
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
             required_len - The number of values we need to compare against

        After finding the proper data, expand it to the required_length by
        repeating the final value.

        @todo: CPI inflate the final value to fill instead of simply repeating
        """

        base_param = self._default_params[param_id]
        base_col = base_param.col_fields[col]

        if is_number(comp_key):
            comp_data = [comp_key]
            source = "the static value"
        elif comp_key == 'default':
            comp_data = base_col.values
            source = "this field's default"
        elif comp_key in self._default_params:
            other_param = self._default_params[comp_key]
            other_col = other_param.col_fields[col]
            other_values = None

            if other_col.id in self.cleaned_data:
                other_values_raw = self.cleaned_data[other_col.id]
                other_values = string_to_float_array(other_values_raw)

            if other_values:
                comp_data = other_values
                source = other_param.name + "'s value"
            else:
                other_defaults = other_col.values
                comp_data = other_defaults
                source = other_param.name + "'s default"
        else:
            raise ValueError('Unknown comp keyword "{0}"'.format(comp_key))

        if len(comp_data) < 1:
            raise ValueError('No comparison data found for kw'.format(comp_key))

        len_diff = required_length - len(comp_data)
        if len_diff > 0:
            comp_data += [comp_data[-1]] * len_diff

        return {'source': source, 'comp_data': comp_data}

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

            if param.max is None and param.min is None:
                continue

            for col, col_field in enumerate(param.col_fields):
                submitted_col_values_raw = self.cleaned_data[col_field.id]
                submitted_col_values = string_to_float_array(submitted_col_values_raw)
                default_col_values = col_field.values

                # If we change a different field which this field relies on for
                # validation, we must ensure this is validated even if unchanged
                # from defaults
                if submitted_col_values:
                    col_values = submitted_col_values
                else:
                    col_values = default_col_values

                if param.max is not None:
                    comp = self.get_comp_data(param.max, param_id, col, len(col_values))
                    source = comp['source']
                    maxes = comp['comp_data']

                    for i, value in enumerate(col_values):
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
                    comp = self.get_comp_data(param.min, param_id, col, len(col_values))
                    source = comp['source']
                    mins = comp['comp_data']

                    for i, value in enumerate(col_values):
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
        model = DynamicSaveInputs
        exclude = ['creation_date']
        widgets = {}
        labels = {}
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
