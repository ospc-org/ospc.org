# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0016_auto_20141021_1952'),
    ]

    operations = [
        migrations.AddField(
            model_name='alternativeminimuminputs',
            name='amt_amount',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alternativeminimuminputs',
            name='amt_phase_out',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alternativeminimuminputs',
            name='amt_phase_out_start',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alternativeminimuminputs',
            name='amt_rate',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alternativeminimuminputs',
            name='individual_surtax',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alternativeminimuminputs',
            name='individual_threshold',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
    ]
