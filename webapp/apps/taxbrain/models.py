from django.db import models
from django.contrib.postgres.fields import ArrayField
from ..core.models import CoreInputs, CoreRun

import taxcalc

from . import param_formatters

from .behaviors import Fieldable, DataSourceable


class TaxSaveInputs(DataSourceable, Fieldable, CoreInputs):
    """
    This model contains all the parameters for the tax model and the tax
    result.

    For filing status fields:
    _0 = Single, _1 = Married filing Jointly, _2 = Married filing Separately,
    _3 = Head of Household (example: _SS_thd50_0 is the Single filing
    status for Income Threshold 1 in the Social Security Tax section.)
    The exception to this rule is for EITC, where:
    _0 = 0 Kids, _1 = 1 Kid, _2 = 2 Kids, & _3 = 3+ Kids
    """

    # Parameters used for Social Security.
    # Record whether or not this was a quick calculation on a sample of data
    quick_calc = models.BooleanField(default=False)

    # deprecated fields list
    deprecated_fields = ArrayField(
        models.CharField(max_length=100, blank=True),
        blank=True,
        null=True
    )

    NONPARAM_FIELDS = set(["id", "quick_calc", "data_source"])

    def set_fields(self):
        """
        Parse raw fields
            1. Only keep fields that user specifies
            2. Map TB names to TC names
            3. Do more specific type checking--in particular, check if
               field is the type that Tax-Calculator expects from this param
            4. Remove errors on undisplayed parameters
        """
        Fieldable.set_fields(self, [taxcalc.Policy, taxcalc.Behavior],
                             nonparam_fields=self.NONPARAM_FIELDS.union(
                                f.name
                                for f in CoreInputs._meta.get_fields()))

    def get_model_specs(self):
        """
        Build JSON model specifications up from fields data

        returns: reform_dict, assumptions_dict, errors_warnings
        """
        behv_fields = {}
        pol_fields = {}
        for k, v in self.gui_field_inputs.items():
            if k.startswith('_BE_'):
                behv_fields[k] = v
            else:
                pol_fields[k] = v

        (reform_dict, assumptions_dict, reform_inputs, assumption_inputs,
            errors_warnings) = param_formatters.get_reform_from_gui(
            self.start_year,
            taxbrain_fields=pol_fields,
            behavior_fields=behv_fields,
            use_puf_not_cps=self.use_puf_not_cps
        )
        Fieldable.pop_extra_errors(self, errors_warnings)
        print(reform_dict, assumptions_dict)
        return (reform_dict, assumptions_dict, reform_inputs,
                assumption_inputs, errors_warnings)

    @property
    def start_year(self):
        # alias for first_year
        return self.first_year

    class Meta:
        permissions = (
            ("view_inputs", "Allowed to view Taxbrain."),
        )


class TaxBrainRun(CoreRun):
    inputs = models.OneToOneField(TaxSaveInputs, related_name='outputs')

    def zip_filename(self):
        return 'taxbrain.zip'
