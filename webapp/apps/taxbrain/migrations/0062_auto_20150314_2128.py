# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0061_auto_20150311_1612'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='fica',
            new_name='_FICA_trt',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='max_taxable_earn',
            new_name='_SS_Income_c',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='soc_max_rate_1',
            new_name='_SS_percentage1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='soc_max_rate_2',
            new_name='_SS_percentage2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='soc_income_threshold_1_single',
            new_name='_SS_thd50_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='soc_income_threshold_1_jointly',
            new_name='_SS_thd50_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='soc_income_threshold_1_head',
            new_name='_SS_thd50_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='soc_income_threshold_1_separately',
            new_name='_SS_thd50_3',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='soc_income_threshold_2_single',
            new_name='_SS_thd85_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='soc_income_threshold_2_jointly',
            new_name='_SS_thd85_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='soc_income_threshold_2_head',
            new_name='_SS_thd85_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='soc_income_threshold_2_separately',
            new_name='_SS_thd85_3',
        ),
    ]
