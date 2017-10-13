# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic', '0016_auto_20171012_1733'),
    ]

    operations = [
        migrations.AddField(
            model_name='dynamicelasticitysaveinputs',
            name='small_open',
            field=models.NullBooleanField(default=None),
        ),
        migrations.AddField(
            model_name='dynamicelasticitysaveinputs',
            name='world_int_rate',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
    ]
