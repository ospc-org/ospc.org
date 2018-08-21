import uuid

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from django.contrib.postgres.fields import JSONField, ArrayField

import taxcalc

from ..btax.models import CommaSeparatedField, SeparatedValuesField

from ..core.models import CoreInputs, CoreRun
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

    # Starting Year of the reform calculation
    first_year = models.IntegerField(default=None, null=True)
    creation_date = models.DateTimeField(
        default=make_aware(datetime.datetime(2015, 1, 1))
    )
    micro_run = models.ForeignKey(TaxBrainRun, blank=True, null=True,
                                  on_delete=models.SET_NULL)

    class Meta:
        permissions = (
            ("view_inputs", "Allowed to view Taxbrain."),
        )


class TaxBrainElastRun(CoreRun):
    inputs = models.OneToOneField(DynamicElasticitySaveInputs,
                                  related_name='outputs')


    def get_absolute_url(self):
        kwargs = {
            'pk': self.pk
        }
        # TODO: Generalize away from TB
        return reverse('elast_output_detail', kwargs=kwargs)

    def get_absolute_edit_url(self):
        kwargs = {
            'pk': self.pk
        }
        # TODO: Generalize away from TB
        return reverse('edit_dynamic_elastic', kwargs=kwargs)

    def zip_filename(self):
        return 'taxbrain.zip'
