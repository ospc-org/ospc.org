import uuid

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from django.contrib.postgres.fields import JSONField, ArrayField

import taxcalc

from ..btax.models import CommaSeparatedField, SeparatedValuesField

from ..taxbrain.models import TaxBrainRun
from ..taxbrain.behaviors import (Fieldable, DataSourceable)
from ..taxbrain import param_formatters

import datetime
from django.utils.timezone import make_aware


class DynamicElasticitySaveInputs(DataSourceable, models.Model):
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
    creation_date = models.DateTimeField(
        default=make_aware(datetime.datetime(2015, 1, 1))
    )

    micro_run = models.ForeignKey(TaxBrainRun, blank=True, null=True,
                                  on_delete=models.SET_NULL)

    class Meta:
        permissions = (
            ("view_inputs", "Allowed to view Taxbrain."),
        )


class DynamicElasticityOutputUrl(models.Model):
    """
    This model creates a unique url for the elasticity of gdp dyn. sim
    """
    unique_inputs = models.ForeignKey(
        DynamicElasticitySaveInputs, default=None)
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
    taxcalc_vers = models.CharField(blank=True, default=None, null=True,
                                    max_length=50)
    webapp_vers = models.CharField(blank=True, default=None, null=True,
                                   max_length=50)

    def get_absolute_url(self):
        kwargs = {
            'pk': self.pk
        }
        return reverse('output_detail', kwargs=kwargs)
