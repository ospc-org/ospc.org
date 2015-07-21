# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0059_auto_20150311_1421'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='personal_exemp_amount',
            field=models.CharField(blank=True, max_length=1000, null=True, validators=[django.core.validators.RegexValidator(regex=b'\\d*\\.\\d+|\\d+', message=b'Enter only numbers separated by commas.')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='phase_out',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=0.02, max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
    ]
