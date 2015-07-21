# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0019_auto_20141021_1953'),
    ]

    operations = [
        migrations.AddField(
            model_name='standarddeductionsinputs',
            name='additional_aged',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='standarddeductionsinputs',
            name='standard_amount',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
    ]
