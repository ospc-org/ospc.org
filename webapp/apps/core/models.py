from django.db import models
from django.contrib.postgres.fields import JSONField


class TaxSimulation(models.Model):
    inputs = JSONField()
    outputs = JSONField(default=None, blank=True, null=True)
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        max_length=32,
        unique=True)
    user = models.ForeignKey(User, default=None, blank=True, null=True)
