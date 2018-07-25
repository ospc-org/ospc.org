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


class JSONReformTaxCalculator(models.Model):
    '''
    This class holds all of the text for a JSON-based reform input
    for TaxBrain. A TaxSavesInput Model will have a foreign key to
    an instance of this model if the user created the TaxBrain job
    through the JSON iput page.
    '''
    reform_text = models.TextField(blank=True, null=False)
    raw_reform_text = models.TextField(blank=True, null=False)
    assumption_text = models.TextField(blank=True, null=False)
    raw_assumption_text = models.TextField(blank=True, null=False)
    errors_warnings_text = models.TextField(blank=True, null=False)

    def get_errors_warnings(self):
        """
        Errors were only stored for the taxcalc.Policy class until PB 1.6.0
        This method ensures that old runs are parsed correctly
        """
        ew = json.loads(self.errors_warnings_text)
        if 'errors' in ew:
            return {'policy': ew}
        else:
            return ew


class CoreInputs(models.Model):
    # Starting Year of the reform calculation
    first_year = models.IntegerField(default=None, null=True)
    # JSON input text
    json_text = models.ForeignKey(
        JSONReformTaxCalculator,
        null=True,
        default=None,
        blank=True)
    # Record whether or not this was a quick calculation on a sample of data
    quick_calc = models.BooleanField(default=False)
    # Creation DateTime
    creation_date = models.DateTimeField(
        default=make_aware(datetime.datetime(2015, 1, 1))
    )
    # validated gui input
    input_fields = JSONField(default=None, blank=True, null=True)
    # raw gui input
    raw_input_fields = JSONField(default=None, blank=True, null=True)


class CoreRun(models.Model):
    inputs = models.OneToOneField(
        CoreInputs,
        on_delete=models.CASCADE
    )
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

    def get_absolute_url(self):
        kwargs = {
            'pk': self.pk
        }
        return reverse('output_detail', kwargs=kwargs)
