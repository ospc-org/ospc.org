# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0015_auto_20141021_1952'),
    ]

    operations = [
        migrations.AddField(
            model_name='creditsinputs',
            name='child_max_credit',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='creditsinputs',
            name='child_phase_out_rate',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='creditsinputs',
            name='child_phase_out_threshold',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='creditsinputs',
            name='eitc_credit_rate',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='creditsinputs',
            name='eitc_phase_out_rate',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='creditsinputs',
            name='eitc_phase_out_threshold',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
    ]
