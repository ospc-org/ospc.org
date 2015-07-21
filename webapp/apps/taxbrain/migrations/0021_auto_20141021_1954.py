# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0020_auto_20141021_1954'),
    ]

    operations = [
        migrations.AddField(
            model_name='adjustmentsinputs',
            name='alimony_paid',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adjustmentsinputs',
            name='archer_msa_deduc',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adjustmentsinputs',
            name='deduc_half_self_employ',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adjustmentsinputs',
            name='foreign_earned_inc_exemp',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adjustmentsinputs',
            name='foreign_housing_adjust',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adjustmentsinputs',
            name='forfeit_int_penalty',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adjustmentsinputs',
            name='keogh_sep_deduc',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adjustmentsinputs',
            name='moving_exp_deduc',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adjustmentsinputs',
            name='other_adjust',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adjustmentsinputs',
            name='reservist_performing_artist',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adjustmentsinputs',
            name='self_employ_health_deduc',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adjustmentsinputs',
            name='student_loan_deduc',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adjustmentsinputs',
            name='total_ira_deduc',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
    ]
