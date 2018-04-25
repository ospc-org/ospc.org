# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0024_taxsaveinputs_quick_calc'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_rt1',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_rt2',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_rt3',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_thd1_0',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_thd1_1',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_thd1_2',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_thd1_3',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_thd1_cpi',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_thd2_0',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_thd2_1',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_thd2_2',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_thd2_3',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_thd2_cpi',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_thd3_0',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_thd3_1',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_thd3_2',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_thd3_3',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='Dividend_thd3_cpi',
        ),
    ]
