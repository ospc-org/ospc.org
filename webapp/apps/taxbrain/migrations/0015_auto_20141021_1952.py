# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0014_auto_20141021_1901'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='personalexemptionsinputs',
            name='exemp_start',
        ),
        migrations.RemoveField(
            model_name='personalexemptionsinputs',
            name='personal_exemp',
        ),
        migrations.AddField(
            model_name='personalexemptionsinputs',
            name='amount',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='personalexemptionsinputs',
            name='phase_out_threshold',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='personalexemptionsinputs',
            name='phase_out',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
    ]
