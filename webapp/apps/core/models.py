from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User
import datetime
from django.utils.timezone import make_aware
from django.core.urlresolvers import reverse
import uuid


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


class CoreInputs(models.Model):
    class Meta:
        abstract = True


class CoreRun(models.Model):
    # Subclasses must implement:
    # inputs = models.OneToOneField(CoreInputs)
    renderable_outputs = JSONField(default=None, blank=True, null=True)
    download_only_outputs = JSONField(default=None, blank=True, null=True)
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
    job_ids = SeparatedValuesField(blank=True, default=None, null=True)
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
