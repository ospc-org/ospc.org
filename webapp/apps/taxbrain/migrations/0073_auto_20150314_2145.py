# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0072_auto_20150314_2144'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividend_rate_three',
            new_name='_Dividend_rt3',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividends_threshold_three_single',
            new_name='_Dividend_thd3_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividends_threshold_three_jointly',
            new_name='_Dividend_thd3_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividends_threshold_three_head',
            new_name='_Dividend_thd3_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividends_threshold_three_separately',
            new_name='_Dividend_thd3_3',
        ),
    ]
