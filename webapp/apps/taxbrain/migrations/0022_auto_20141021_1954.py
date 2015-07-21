# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0021_auto_20141021_1954'),
    ]

    operations = [
        migrations.AddField(
            model_name='grossincomeinputs',
            name='rate_one',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='grossincomeinputs',
            name='rate_two',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='grossincomeinputs',
            name='threshold_one',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='grossincomeinputs',
            name='threshold_two',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
    ]
