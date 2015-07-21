# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0058_remove_taxsaveinputs_income_tax_threshold_7'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='personal_exemp_amount',
            field=models.CharField(blank=True, max_length=400, null=True, validators=[django.core.validators.RegexValidator(regex=b'\\d*\\.\\d+|\\d+', message=b'Enter only numbers separated by commas.', code=b'invalid_values')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='phase_out_threshold_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='phase_out_threshold_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='phase_out_threshold_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='phase_out_threshold_single',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
