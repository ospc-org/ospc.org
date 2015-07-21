# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0038_auto_20141222_2249'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='inflation_years',
            field=models.FloatField(default=None, null=True, blank=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='medical_years',
            field=models.FloatField(default=None, null=True, blank=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)]),
            preserve_default=True,
        ),
    ]
