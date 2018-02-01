import re
from distutils.version import LooseVersion

from django.db import models
from django.core import validators
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.auth.models import User

from uuidfield import UUIDField
from jsonfield import JSONField


from ..taxbrain.models import (CommaSeparatedField, SeparatedValuesField,
                               TaxSaveInputs, OutputUrl)

from ..taxbrain.helpers import rename_keys, PRE_TC_0130_RES_MAP

import datetime


class DynamicSaveInputs(models.Model):
    """
    This model contains all the parameters for the dynamic tax model and the tax
    result.

   """

    # Parameters used for the dynamic model
    g_y_annual = CommaSeparatedField(default=None, null=True, blank=True)
    g_y_annual_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    upsilon = CommaSeparatedField(default=None, null=True, blank=True)
    upsilon_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    frisch = CommaSeparatedField(default=None, null=True, blank=True)

    # Job IDs when running a job
    job_ids = SeparatedValuesField(blank=True, default=None, null=True)
    # Globally unique ID for an output path when running a job
    guids = SeparatedValuesField(blank=True, default=None, null=True)

    # Starting Year of the reform calculation
    first_year = models.IntegerField(default=None, null=True)
    # Result
    tax_result = JSONField(default=None, blank=True, null=True)
    # Creation DateTime
    creation_date = models.DateTimeField(default=datetime.datetime(2015, 1, 1))
    # Email address for user who started this job
    user_email = models.CharField(blank=True, default=None, null=True,
                                  max_length=50)

    micro_sim = models.ForeignKey(OutputUrl, blank=True, null=True,
                                  on_delete=models.SET_NULL)

    class Meta:
        permissions = (
            ("view_inputs", "Allowed to view Taxbrain."),
        )


class DynamicBehaviorSaveInputs(models.Model):
    """
    This model contains all the parameters for the dynamic behavioral tax
    model and the tax result.

   """

    # Behavioral Effects
    BE_inc = CommaSeparatedField(default=None, blank=True, null=True)
    BE_sub = CommaSeparatedField(default=None, blank=True, null=True)
    BE_cg = CommaSeparatedField(default=None, blank=True, null=True)
    BE_CG_trn = CommaSeparatedField(default=None, blank=True, null=True)
    BE_charity_itemizers = CommaSeparatedField(default=None, blank=True, null=True)
    BE_charity_non_itemizers = CommaSeparatedField(default=None, blank=True, null=True)
    BE_charity_0 = CommaSeparatedField(default=None, blank=True, null=True)
    BE_charity_1 = CommaSeparatedField(default=None, blank=True, null=True)
    BE_charity_2 = CommaSeparatedField(default=None, blank=True, null=True)
    BE_subinc_wrt_earnings = CommaSeparatedField(default=None, blank=True, null=True)

    # Job IDs when running a job
    job_ids = SeparatedValuesField(blank=True, default=None, null=True)
    jobs_not_ready = SeparatedValuesField(blank=True, default=None, null=True)

    # Starting Year of the reform calculation
    first_year = models.IntegerField(default=None, null=True)
    # Result
    tax_result = JSONField(default=None, blank=True, null=True)
    # Creation DateTime
    creation_date = models.DateTimeField(default=datetime.datetime(2015, 1, 1))

    micro_sim = models.ForeignKey(OutputUrl, blank=True, null=True,
                                  on_delete=models.SET_NULL)

    def get_tax_result(self):
        """
        If taxcalc version is greater than or equal to 0.13.0, return table
        If taxcalc version is less than 0.13.0, then rename keys to new names
        and then return table
        """
        outputurl = DynamicBehaviorOutputUrl.objects.get(unique_inputs__pk=self.pk)
        taxcalc_vers = outputurl.taxcalc_vers
        # only the older (pre 0.13.0) taxcalc versions are null
        if taxcalc_vers:
            taxcalc_vers = LooseVersion(taxcalc_vers)
        else:
            return rename_keys(self.tax_result, PRE_TC_0130_RES_MAP)

        # older PB versions stored commit reference too
        # e.g. taxcalc_vers = "0.9.0.d79abf"
        if taxcalc_vers >= LooseVersion("0.13.0"):
            return self.tax_result
        else:
            return rename_keys(self.tax_result, PRE_TC_0130_RES_MAP)

    class Meta:
        permissions = (
            ("view_inputs", "Allowed to view Taxbrain."),
        )


class DynamicElasticitySaveInputs(models.Model):
    """
    This model contains all the parameters for the dynamic elasticity
    wrt GDP dynamic macro model and tax result
    """

    # Elasticity of GDP w.r.t. average marginal tax rates
    elastic_gdp = CommaSeparatedField(default=None, blank=True, null=True)

    # Job IDs when running a job
    job_ids = SeparatedValuesField(blank=True, default=None, null=True)
    jobs_not_ready = SeparatedValuesField(blank=True, default=None, null=True)

    # Starting Year of the reform calculation
    first_year = models.IntegerField(default=None, null=True)
    # Result
    tax_result = JSONField(default=None, blank=True, null=True)
    # Creation DateTime
    creation_date = models.DateTimeField(default=datetime.datetime(2015, 1, 1))

    micro_sim = models.ForeignKey(OutputUrl, blank=True, null=True,
                                  on_delete=models.SET_NULL)

    class Meta:
        permissions = (
            ("view_inputs", "Allowed to view Taxbrain."),
        )


class OGUSAWorkerNodesCounter(models.Model):
    '''
    This class specifies a counter for which OGUSA node we have
    just deployed an OGUSA job to. It is a singleton class to enforce
    round robin behavior with multiple dynos running simultaneously. The
    database becomes the single source of truth for which node
    just got the last dispatch
    '''
    singleton_enforce = models.IntegerField(default=1, unique=True)
    current_idx = models.IntegerField(default=0)


class DynamicOutputUrl(models.Model):
    """
    This model creates a unique url for each calculation.
    """
    unique_inputs = models.ForeignKey(DynamicSaveInputs, default=None)
    user = models.ForeignKey(User, null=True, default=None)
    model_pk = models.IntegerField(default=None, null=True)
    uuid = UUIDField(auto=True, default=None, null=True)
    ogusa_vers = models.CharField(blank=True, default=None, null=True,
        max_length=50)
    webapp_vers = models.CharField(blank=True, default=None, null=True,
        max_length=50)

    def get_absolute_url(self):
        kwargs = {
            'pk': self.pk
        }
        return reverse('output_detail', kwargs=kwargs)


class DynamicBehaviorOutputUrl(models.Model):
    """
    This model creates a unique url for the partial equilibrium
    """
    unique_inputs = models.ForeignKey(DynamicBehaviorSaveInputs, default=None)
    user = models.ForeignKey(User, null=True, default=None)
    model_pk = models.IntegerField(default=None, null=True)
    # Expected Completion DateTime
    exp_comp_datetime = models.DateTimeField(default=datetime.datetime(2015, 1, 1))
    uuid = UUIDField(auto=True, default=None, null=True)
    taxcalc_vers = models.CharField(blank=True, default=None, null=True,
        max_length=50)
    webapp_vers = models.CharField(blank=True, default=None, null=True,
        max_length=50)

    def get_absolute_url(self):
        kwargs = {
            'pk': self.pk
        }
        return reverse('output_detail', kwargs=kwargs)


class DynamicElasticityOutputUrl(models.Model):
    """
    This model creates a unique url for the elasticity of gdp dyn. sim
    """
    unique_inputs = models.ForeignKey(DynamicElasticitySaveInputs, default=None)
    user = models.ForeignKey(User, null=True, default=None)
    model_pk = models.IntegerField(default=None, null=True)
    # Expected Completion DateTime
    exp_comp_datetime = models.DateTimeField(default=datetime.datetime(2015, 1, 1))
    uuid = UUIDField(auto=True, default=None, null=True)
    taxcalc_vers = models.CharField(blank=True, default=None, null=True,
        max_length=50)
    webapp_vers = models.CharField(blank=True, default=None, null=True,
        max_length=50)


    def get_absolute_url(self):
        kwargs = {
            'pk': self.pk
        }
        return reverse('output_detail', kwargs=kwargs)
