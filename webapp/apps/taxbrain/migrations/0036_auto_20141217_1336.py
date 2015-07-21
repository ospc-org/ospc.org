# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0035_auto_20141125_1711'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='inflation',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='medical_inflation',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='personal_exemp_amount',
            field=models.FloatField(default=None, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='phase_out_threshold',
            field=models.FloatField(default=None, null=True),
            preserve_default=True,
        ),
    ]
