# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuidfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0030_auto_20141022_2209'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='outputurl',
            name='slug',
        ),
        migrations.AddField(
            model_name='outputurl',
            name='uuid',
            field=uuidfield.fields.UUIDField(null=True, default=None, editable=False, max_length=32, blank=True, unique=True),
            preserve_default=True,
        ),
    ]
