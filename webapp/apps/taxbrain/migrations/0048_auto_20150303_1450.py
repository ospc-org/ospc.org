# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0047_taxsaveinputs_max_taxable_earn'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='soc_income_threshold_1',
            new_name='soc_income_threshold_1_head',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='soc_income_threshold_2',
            new_name='soc_income_threshold_2_single',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='soc_income_threshold_1_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='soc_income_threshold_1_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='soc_income_threshold_1_single',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='soc_income_threshold_2_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='soc_income_threshold_2_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='soc_income_threshold_2_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
