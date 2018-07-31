from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User
import datetime
from django.utils.timezone import make_aware
from django.core.urlresolvers import reverse
import uuid


class CoreInputs(models.Model):
    # Raw GUI input
    raw_input_fields = JSONField(default=None, blank=True, null=True)

    # Validated GUI input that has been parsed to have the correct data types
    input_fields = JSONField(default=None, blank=True, null=True)

    class Meta:
        abstract = True


class CoreRun(models.Model):
    # Subclasses must implement:
    # inputs = models.OneToOneField(CoreInputs)
    outputs = JSONField(default=None, blank=True, null=True)
    uuid = models.UUIDField(
        default=uuid.uuid1,
        editable=False,
        max_length=32,
        unique=True,
        primary_key=True)
    error_text = models.CharField(
        null=False,
        blank=True,
        max_length=4000)
    user = models.ForeignKey(User, null=True, default=None)
    exp_comp_datetime = models.DateTimeField(
        default=make_aware(datetime.datetime(2015, 1, 1)))
    job_id = models.UUIDField(blank=True, default=None, null=True)
    upstream_vers = models.CharField(blank=True, default=None, null=True,
                                     max_length=50)
    webapp_vers = models.CharField(blank=True, default=None, null=True,
                                   max_length=50)

    def get_absolute_url(self):
        kwargs = {
            'pk': self.pk
        }
        return reverse('output_detail', kwargs=kwargs)

    class Meta:
        abstract = True
