# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0036_auto_20141217_1336'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='inflation',
            field=models.FloatField(default=None, null=True, blank=True, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='medical_inflation',
            field=models.FloatField(default=None, null=True, blank=True, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)]),
            preserve_default=True,
        ),
    ]
