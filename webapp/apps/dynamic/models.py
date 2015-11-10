import re

from django.db import models
from django.core import validators
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.auth.models import User

from uuidfield import UUIDField
from jsonfield import JSONField


from ..taxbrain.models import CommaSeparatedField, SeparatedValuesField
import datetime


class DynamicSaveInputs(models.Model):
    """
    This model contains all the parameters for the dynamic tax model and the tax
    result.

   """

    # Parameters used for the dynamic model
    g_y_annual = CommaSeparatedField(default=None, null=True, blank=True)
    upsilon = CommaSeparatedField(default=None, null=True, blank=True)

    # Job IDs when running a job
    job_ids = SeparatedValuesField(blank=True, default=None, null=True)

    # Starting Year of the reform calculation
    first_year = models.IntegerField(default=None, null=True)
    # Result
    tax_result = JSONField(default=None, blank=True, null=True)
    # Creation DateTime
    creation_date = models.DateTimeField(default=datetime.datetime(2015, 1, 1))

    class Meta:
        permissions = (
            ("view_inputs", "Allowed to view Taxbrain."),
        )


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

    def get_absolute_url(self):
        kwargs = {
            'pk': self.pk
        }
        return reverse('output_detail', kwargs=kwargs)
