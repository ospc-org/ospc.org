# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0070_auto_20150314_2142'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividend_rate_one',
            new_name='_Dividend_rt1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividends_threshold_one_single',
            new_name='_Dividend_thd1_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividends_threshold_one_jointly',
            new_name='_Dividend_thd1_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividends_threshold_one_head',
            new_name='_Dividend_thd1_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividends_threshold_one_separately',
            new_name='_Dividend_thd1_3',
        ),
    ]
