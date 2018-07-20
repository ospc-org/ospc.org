from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User
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

class CoreRun(models.Model):
    inputs = JSONField()
    outputs = JSONField(default=None, blank=True, null=True)
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        max_length=32,
        unique=True)
    user = models.ForeignKey(User, default=None, blank=True, null=True)
    job_ids = SeparatedValuesField(blank=True, default=None, null=True)

    def get_model_specs(self):
        """
        Build JSON model specifications up from fields data

        returns: reform_dict, assumptions_dict, errors_warnings
        """
        (reform_dict, assumptions_dict, reform_text, assumptions_text,
            errors_warnings) = param_formatters.get_reform_from_gui(
            self.start_year,
            taxbrain_fields=self.input_fields,
            use_puf_not_cps=self.use_puf_not_cps
        )
        Fieldable.pop_extra_errors(self, errors_warnings)
        return (reform_dict, assumptions_dict, reform_text, assumptions_text,
                errors_warnings)

    def set_fields(self):
        """
        Parse raw fields
            1. Only keep fields that user specifies
            2. Map TB names to TC names
            3. Do more specific type checking--in particular, check if
               field is the type that Tax-Calculator expects from this param
            4. Remove errors on undisplayed parameters
        """
        Fieldable.set_fields(self, taxcalc.Policy,
                             nonparam_fields=self.NONPARAM_FIELDS)

    class Meta:
        abstract = True


class TaxBrainRun(CoreRun):
    pass
