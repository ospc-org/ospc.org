from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User
import uuid


class CoreRun(models.Model):
    outputs = JSONField(default=None, blank=True, null=True)
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        max_length=32,
        unique=True)
