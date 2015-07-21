# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0053_auto_20150303_1459'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividends_threshold_one',
            new_name='dividends_threshold_one_single',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividends_threshold_three',
            new_name='dividends_threshold_three_single',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='dividends_threshold_two',
            new_name='dividends_threshold_two_single',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='net_invest_income_threshold',
            new_name='net_invest_income_threshold_single',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='dividends_threshold_one_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='dividends_threshold_one_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='dividends_threshold_one_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='dividends_threshold_three_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='dividends_threshold_three_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='dividends_threshold_three_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='dividends_threshold_two_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='dividends_threshold_two_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='dividends_threshold_two_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='net_invest_income_threshold_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='net_invest_income_threshold_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='net_invest_income_threshold_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
