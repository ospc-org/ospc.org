# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriber',
            name='active',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='subscriber',
            name='confirm_key',
            field=models.UUIDField(default=uuid.uuid4),
        ),
        migrations.AddField(
            model_name='subscriber',
            name='subscribe_date',
            field=models.DateField(default=datetime.datetime(2015, 7, 2, 1, 47, 37, 472513, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
    ]
