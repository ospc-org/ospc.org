import uuid

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core import validators
from django.core.validators import MaxValueValidator, MinValueValidator

import datetime
from django.utils.timezone import make_aware

# digit or true/false (case insensitive)
COMMASEP_REGEX = "(<,)|(\\d*\\.\\d+|\\d+)|((?i)(true|false))"


class CommaSeparatedField(models.CharField):
    default_validators = [validators.RegexValidator(regex=COMMASEP_REGEX)]
    description = "A comma separated field that allows multiple floats."

    def __init__(self, verbose_name=None, name=None, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 200)
        super(CommaSeparatedField, self).__init__(verbose_name, name, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(
            CommaSeparatedField, self).deconstruct()
        if kwargs.get("max_length", None) == 1000:
            del kwargs['max_length']
        return name, path, args, kwargs

class SeparatedValuesField(models.TextField):

    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token', ',')
        super(SeparatedValuesField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            return
        if isinstance(value, list):
            return value
        return value.split(self.token)

    def get_db_prep_value(self, value, connection=None, prepared=False):
        if not value:
            return
        assert(isinstance(value, list) or isinstance(value, tuple))
        return self.token.join([str(s) for s in value])

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)


class BTaxSaveInputs(models.Model):
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

    btax_betr_corp = CommaSeparatedField(default=None, null=True, blank=True)
    btax_betr_entity_Switch = models.NullBooleanField(
        default=None, blank=True, null=True)
    btax_betr_pass = CommaSeparatedField(default=None, blank=True, null=True)

    btax_depr_allyr = models.CharField(blank=True, default=None, null=True,
                                       max_length=50)

    btax_depr_3yr = models.CharField(blank=True, default=None, null=True,
                                     max_length=50)
    btax_depr_5yr = models.CharField(blank=True, default=None, null=True,
                                     max_length=50)
    btax_depr_7yr = models.CharField(blank=True, default=None, null=True,
                                     max_length=50)
    btax_depr_10yr = models.CharField(blank=True, default=None, null=True,
                                      max_length=50)
    btax_depr_15yr = models.CharField(blank=True, default=None, null=True,
                                      max_length=50)
    btax_depr_20yr = models.CharField(blank=True, default=None, null=True,
                                      max_length=50)
    btax_depr_25yr = models.CharField(blank=True, default=None, null=True,
                                      max_length=50)
    btax_depr_27_5yr = models.CharField(blank=True, default=None, null=True,
                                        max_length=50)
    btax_depr_39yr = models.CharField(blank=True, default=None, null=True,
                                      max_length=50)

    btax_depr_allyr_gds_Switch = models.CharField(
        default="True", blank=True, null=True, max_length=50)
    btax_depr_3yr_gds_Switch = models.CharField(
        default="True", blank=True, null=True, max_length=50)
    btax_depr_5yr_gds_Switch = models.CharField(
        default="True", blank=True, null=True, max_length=50)
    btax_depr_7yr_gds_Switch = models.CharField(
        default="True", blank=True, null=True, max_length=50)
    btax_depr_10yr_gds_Switch = models.CharField(
        default="True", blank=True, null=True, max_length=50)
    btax_depr_15yr_gds_Switch = models.CharField(
        default="True", blank=True, null=True, max_length=50)
    btax_depr_20yr_gds_Switch = models.CharField(
        default="True", blank=True, null=True, max_length=50)
    btax_depr_25yr_gds_Switch = models.CharField(
        default="True", blank=True, null=True, max_length=50)
    btax_depr_27_5yr_gds_Switch = models.CharField(
        default="True", blank=True, null=True, max_length=50)
    btax_depr_39yr_gds_Switch = models.CharField(
        default="True", blank=True, null=True, max_length=50)

    btax_depr_allyr_ads_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_3yr_ads_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_5yr_ads_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_7yr_ads_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_10yr_ads_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_15yr_ads_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_20yr_ads_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_25yr_ads_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_27_5yr_ads_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_39yr_ads_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)

    btax_depr_allyr_tax_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_3yr_tax_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_5yr_tax_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_7yr_tax_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_10yr_tax_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_15yr_tax_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_20yr_tax_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_25yr_tax_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_27_5yr_tax_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)
    btax_depr_39yr_tax_Switch = models.CharField(
        default="False", blank=True, null=True, max_length=50)

    btax_depr_allyr_exp = CommaSeparatedField(
        default=None, null=True, blank=True)
    btax_depr_3yr_exp = CommaSeparatedField(
        default=None, null=True, blank=True)
    btax_depr_5yr_exp = CommaSeparatedField(
        default=None, null=True, blank=True)
    btax_depr_7yr_exp = CommaSeparatedField(
        default=None, null=True, blank=True)
    btax_depr_10yr_exp = CommaSeparatedField(
        default=None, null=True, blank=True)
    btax_depr_15yr_exp = CommaSeparatedField(
        default=None, null=True, blank=True)
    btax_depr_20yr_exp = CommaSeparatedField(
        default=None, null=True, blank=True)
    btax_depr_25yr_exp = CommaSeparatedField(
        default=None, null=True, blank=True)
    btax_depr_27_5yr_exp = CommaSeparatedField(
        default=None, null=True, blank=True)
    btax_depr_39yr_exp = CommaSeparatedField(
        default=None, null=True, blank=True)

    btax_other_hair = CommaSeparatedField(default=None, null=True, blank=True)
    btax_other_corpeq = CommaSeparatedField(
        default=None, null=True, blank=True)
    btax_other_proptx = CommaSeparatedField(
        default=None, null=True, blank=True)
    btax_other_invest = CommaSeparatedField(
        default=None, null=True, blank=True)
    btax_econ_nomint = CommaSeparatedField(default=None, null=True, blank=True)
    btax_econ_inflat = CommaSeparatedField(default=None, null=True, blank=True)

    # Job IDs when running a job
    job_id = models.UUIDField(blank=True, default=None, null=True)

    # Starting Year of the reform calculation
    first_year = models.IntegerField(default=None, null=True)
    # data source for model
    data_source = models.CharField(
        default="PUF",
        blank=True,
        null=True,
        max_length=20)
    # Result
    tax_result = models.TextField(default=None, blank=True, null=True)
    # Creation DateTime
    creation_date = models.DateTimeField(
        default=make_aware(datetime.datetime(2015, 1, 1))
    )

    class Meta:
        permissions = (
            ("view_inputs", "Allowed to view Taxbrain."),
        )


class BTaxOutputUrl(models.Model):
    """
    This model creates a unique url for each calculation.
    """
    unique_inputs = models.ForeignKey(BTaxSaveInputs, default=None)
    user = models.ForeignKey(User, null=True, default=None)
    model_pk = models.IntegerField(default=None, null=True)
    # Expected Completion DateTime
    exp_comp_datetime = models.DateTimeField(
        default=make_aware(datetime.datetime(2015, 1, 1))
    )
    uuid = models.UUIDField(
        default=uuid.uuid4,
        null=True,
        editable=False,
        max_length=32,
        blank=True,
        unique=True)
    btax_vers = models.CharField(
        blank=True,
        default=None,
        null=True,
        max_length=50)
    taxcalc_vers = models.CharField(
        blank=True, default=None, null=True, max_length=50)
    webapp_vers = models.CharField(blank=True, default=None, null=True,
                                   max_length=50)

    def get_absolute_url(self):
        kwargs = {
            'pk': self.pk
        }
        return reverse('btax_output_detail', kwargs=kwargs)
