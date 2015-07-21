# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0027_auto_20141022_1559'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='additional_aged',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='alimony_paid',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='amt_amount',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='amt_phase_out',
            field=models.FloatField(default=0.025, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='amt_phase_out_start',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='amt_rate',
            field=models.FloatField(default=0.26, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='archer_msa_deduc',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='casualty_floor',
            field=models.FloatField(default=0.1, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='charity_ceiling_assets',
            field=models.FloatField(default=0.3, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='charity_ceiling_cash',
            field=models.FloatField(default=0.5, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='child_max_credit',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='child_phase_out_rate',
            field=models.FloatField(default=0.05, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='child_phase_out_threshold',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='deduc_half_self_employ',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='dividends',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='eitc_credit_rate',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='eitc_phase_out_rate',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='eitc_phase_out_threshold',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='fica',
            field=models.FloatField(default=0.153, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='foreign_earned_inc_exemp',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='foreign_housing_adjust',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='forfeit_int_penalty',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='income_tax_rate',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='individual_surtax',
            field=models.FloatField(default=0.02, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='individual_threshold',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='item_phase_out_rate',
            field=models.FloatField(default=0.03, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='item_phase_out_threshold',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='keogh_sep_deduc',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='long_term_cap',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='max_perc_forfeited',
            field=models.FloatField(default=0.08, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='medical_floor',
            field=models.FloatField(default=0.075, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='medicare_unearned_inc_rate',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='medicare_unearned_inc_threshold',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='misc_floor',
            field=models.FloatField(default=0.02, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='moving_exp_deduc',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='other_adjust',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='rate_one',
            field=models.FloatField(default=0.5, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='rate_two',
            field=models.FloatField(default=0.85, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='reservist_performing_artist',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='self_employ_health_deduc',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='soc_max',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='standard_amount',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='state_haircut',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='state_limit',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='student_loan_deduc',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='threshold_one',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='threshold_two',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='total_ira_deduc',
            field=models.FloatField(default=None, null=True, blank=True),
        ),
    ]
