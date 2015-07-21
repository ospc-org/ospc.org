# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0037_auto_20141222_2218'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='inflation_years',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='medical_years',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
