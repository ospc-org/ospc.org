from django import forms
from django.forms import ModelForm
import six
import json

from ..constants import START_YEAR

from .models import TaxSaveInputs
from .helpers import (is_safe, INPUTS_META, bool_like)
from .param_displayers import defaults_all
from .param_formatters import (get_default_policy_param,
                               ParameterLookUpException)
import taxcalc


class PolicyBrainForm:

    def add_fields(self, args):
        if not args:
            return args
        parsed_data = {}
        args_data = args[0]
        raw_fields = {}
        for k, v in list(args_data.items()):
            if k not in INPUTS_META:
                raw_fields[k] = v
            elif k in ('first_year', 'data_source'):
                parsed_data[k] = v
            else:
                pass
        parsed_data["raw_gui_field_inputs"] = json.dumps(raw_fields)
        parsed_data["gui_field_inputs"] = json.dumps("")
        return (parsed_data,)

    def add_errors_on_extra_inputs(self):
        ALLOWED_EXTRAS = {'has_errors', 'start_year', 'csrfmiddlewaretoken',
                          'data_source'}
        all_inputs = set(self.data.keys())
        allowed_inputs = set(self.fields.keys())
        extra_inputs = all_inputs - allowed_inputs - ALLOWED_EXTRAS

        for _input in extra_inputs:
            self.add_error(None,
                           "Extra input '{0}' not allowed".format(_input))

        all_fields = self.cleaned_data['raw_gui_field_inputs']
        default_params = getattr(self.Meta, 'default_params', None)
        allowed_fields = getattr(self.Meta, 'allowed_fields', None)
        for _field in all_fields:
            if default_params:
                try:
                    get_default_policy_param(_field, default_params)
                except ParameterLookUpException as exn:
                    self.add_error(None, str(exn))
            elif _field not in allowed_fields:
                msg = "Received unexpected parameter: {}".format(_field)
                self.add_error(None, msg)

    def do_taxcalc_validations(self):
        """
        Do minimal type checking to make sure that we did not get any
        malicious input
        """
        fields = self.cleaned_data['raw_gui_field_inputs']
        for param_name, value in fields.items():
            # make sure the text parses OK
            if param_name == 'data_source':
                assert value in ('CPS', 'PUF')
            elif isinstance(value, six.string_types) and len(value) > 0:
                if not is_safe(value):
                    # Parse Error - we don't recognize what they gave us
                    self.add_error(param_name,
                                   "Unrecognized value: {}".format(value))
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

        for param in list(defaults.values()):
            for field in param.col_fields:
                attrs = {
                    'class': 'form-control',
                    'placeholder': field.default_value,
                }
                if param.coming_soon:
                    attrs['disabled'] = True

                if param.tc_id in boolean_fields:
                    checkbox = forms.CheckboxInput(
                        attrs=attrs, check_test=bool_like)
                    widgets[field.id] = checkbox
                    update_fields[field.id] = forms.BooleanField(
                        label=field.label,
                        widget=widgets[field.id],
                        required=False,
                        disabled=param.gray_out
                    )
                else:
                    widgets[field.id] = forms.TextInput(attrs=attrs)
                    update_fields[field.id] = forms.fields.CharField(
                        label=field.label,
                        widget=widgets[field.id],
                        required=False,
                        disabled=param.gray_out
                    )

                labels[field.id] = field.label

            if getattr(param, "inflatable", False):
                field = param.cpi_field
                attrs = {
                    'class': 'form-control sr-only',
                    'placeholder': bool(field.default_value),
                }

                widgets[field.id] = forms.NullBooleanSelect(attrs=attrs)
                update_fields[field.id] = forms.NullBooleanField(
                    label=field.label,
                    widget=widgets[field.id],
                    required=False,
                    disabled=param.gray_out
                )
        return widgets, labels, update_fields


TAXCALC_DEFAULTS = {
    (int(START_YEAR), True): defaults_all(int(START_YEAR),
                                          use_puf_not_cps=True)
}


class TaxBrainForm(PolicyBrainForm, ModelForm):

    def __init__(self, first_year, use_puf_not_cps, *args, **kwargs):
        # the start year and the data source form object for later access.
        # This should be refactored into `process_model`
        if first_year is None:
            first_year = START_YEAR
        self._first_year = int(first_year)

        # reset form data; form data from the `Meta` class is not updated each
        # time a new `TaxBrainForm` instance is created
        self.set_form_data(self._first_year, use_puf_not_cps)
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
            kwargs["initial"] = kwargs["instance"].raw_gui_field_inputs

        # Update CPI flags if either
        # 1. initial is specified in `kwargs` (reform has warning/error msgs)
        # 2. if `instance` is specified and `initial` is added above
        #    (edit parameters page)
        if "initial" in kwargs:
            for k, v in kwargs["initial"].items():
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

            if not hasattr(self, 'cleaned_data'):
                self.cleaned_data = {'raw_gui_field_inputs': kwargs['initial']}

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
        if getattr(
            self,
            "cleaned_data",
                None) is None or self.cleaned_data is None:
            self.cleaned_data = {}
        ModelForm.add_error(self, field, error)

    def set_form_data(self, start_year, use_puf_not_cps):
        defaults_key = (start_year, use_puf_not_cps)
        if defaults_key not in TAXCALC_DEFAULTS:
            TAXCALC_DEFAULTS[defaults_key] = defaults_all(
                start_year, use_puf_not_cps)
        defaults = TAXCALC_DEFAULTS[defaults_key]
        (self.widgets, self.labels,
            self.update_fields) = PolicyBrainForm.set_form(defaults)

    class Meta:
        model = TaxSaveInputs
        # we are only updating the "first_year", "raw_fields", and "fields"
        # fields
        fields = ['first_year', 'data_source', 'raw_gui_field_inputs',
                  'gui_field_inputs']
        start_year = int(START_YEAR)
        default_policy = taxcalc.Policy.default_data(
            start_year=int(START_YEAR),
            metadata=True
        )
        default_behv = taxcalc.Behavior.default_data(
            start_year=int(START_YEAR),
            metadata=True
        )
        default_params = dict(default_policy, **default_behv)
        defaults_key = (start_year, True)
        if defaults_key not in TAXCALC_DEFAULTS:
            TAXCALC_DEFAULTS[defaults_key] = defaults_all(
                start_year,
                use_puf_not_cps=True
            )
        (widgets, labels,
            update_fields) = PolicyBrainForm.set_form(
            TAXCALC_DEFAULTS[defaults_key]
        )
