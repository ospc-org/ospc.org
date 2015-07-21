# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0071_auto_20150314_2143'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividend_rate_two',
            new_name='_Dividend_rt2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividends_threshold_two_single',
            new_name='_Dividend_thd2_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividends_threshold_two_jointly',
            new_name='_Dividend_thd2_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividends_threshold_two_head',
            new_name='_Dividend_thd2_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividends_threshold_two_separately',
            new_name='_Dividend_thd2_3',
        ),
    ]
