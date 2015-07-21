# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0039_auto_20141222_2305'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='state_limit',
            field=models.CharField(blank=True, max_length=400, null=True, validators=[django.core.validators.RegexValidator(regex=b'\\d*\\.\\d+|\\d+', message=b'Enter only numbers separated by commas.', code=b'invalid_values')]),
            preserve_default=True,
        ),
    ]
