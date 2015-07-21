# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0023_auto_20141021_1954'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaxSaveInputs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fica', models.FloatField(default=None)),
                ('soc_max', models.FloatField(default=None)),
                ('rate_one', models.FloatField(default=None, blank=True)),
                ('threshold_one', models.FloatField(default=None, blank=True)),
                ('rate_two', models.FloatField(default=None, blank=True)),
                ('threshold_two', models.FloatField(default=None, blank=True)),
                ('total_ira_deduc', models.FloatField(default=None, blank=True)),
                ('student_loan_deduc', models.FloatField(default=None, blank=True)),
                ('archer_msa_deduc', models.FloatField(default=None, blank=True)),
                ('deduc_half_self_employ', models.FloatField(default=None, blank=True)),
                ('self_employ_health_deduc', models.FloatField(default=None, blank=True)),
                ('keogh_sep_deduc', models.FloatField(default=None, blank=True)),
                ('forfeit_int_penalty', models.FloatField(default=None, blank=True)),
                ('alimony_paid', models.FloatField(default=None, blank=True)),
                ('moving_exp_deduc', models.FloatField(default=None, blank=True)),
                ('other_adjust', models.FloatField(default=None, blank=True)),
                ('foreign_housing_adjust', models.FloatField(default=None, blank=True)),
                ('reservist_performing_artist', models.FloatField(default=None, blank=True)),
                ('foreign_earned_inc_exemp', models.FloatField(default=None, blank=True)),
                ('standard_amount', models.FloatField(default=None, blank=True)),
                ('additional_aged', models.FloatField(default=None, blank=True)),
                ('medical_floor', models.FloatField(default=None, blank=True)),
                ('state_haircut', models.FloatField(default=None, blank=True)),
                ('state_limit', models.FloatField(default=None, blank=True)),
                ('casualty_floor', models.FloatField(default=None, blank=True)),
                ('misc_floor', models.FloatField(default=None, blank=True)),
                ('charity_ceiling_cash', models.FloatField(default=None, blank=True)),
                ('charity_ceiling_assets', models.FloatField(default=None, blank=True)),
                ('item_phase_out_threshold', models.FloatField(default=None, blank=True)),
                ('item_phase_out_rate', models.FloatField(default=None, blank=True)),
                ('max_perc_forfeited', models.FloatField(default=None, blank=True)),
                ('long_term_cap', models.FloatField(default=None, blank=True)),
                ('dividends', models.FloatField(default=None, blank=True)),
                ('medicare_unearned_inc_rate', models.FloatField(default=None, blank=True)),
                ('medicare_unearned_inc_threshold', models.FloatField(default=None, blank=True)),
                ('income_tax_rate', models.FloatField(default=None, blank=True)),
                ('amt_amount', models.FloatField(default=None, blank=True)),
                ('amt_phase_out', models.FloatField(default=None, blank=True)),
                ('amt_phase_out_start', models.FloatField(default=None, blank=True)),
                ('amt_rate', models.FloatField(default=None, blank=True)),
                ('individual_surtax', models.FloatField(default=None, blank=True)),
                ('individual_threshold', models.FloatField(default=None, blank=True)),
                ('eitc_credit_rate', models.FloatField(default=None, blank=True)),
                ('eitc_phase_out_rate', models.FloatField(default=None, blank=True)),
                ('eitc_phase_out_threshold', models.FloatField(default=None, blank=True)),
                ('child_max_credit', models.FloatField(default=None, blank=True)),
                ('child_phase_out_rate', models.FloatField(default=None, blank=True)),
                ('child_phase_out_threshold', models.FloatField(default=None, blank=True)),
                ('amount', models.FloatField(default=None, null=True, blank=True)),
                ('phase_out', models.FloatField(default=None, null=True, blank=True)),
                ('phase_out_threshold', models.FloatField(default=None, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.DeleteModel(
            name='AdjustmentsInputs',
        ),
        migrations.DeleteModel(
            name='AlternativeMinimumInputs',
        ),
        migrations.DeleteModel(
            name='CreditsInputs',
        ),
        migrations.DeleteModel(
            name='GrossIncomeInputs',
        ),
        migrations.DeleteModel(
            name='IncomeRatesInputs',
        ),
        migrations.DeleteModel(
            name='ItemizedDeductionsInputs',
        ),
        migrations.DeleteModel(
            name='SocialSecurityInputs',
        ),
        migrations.DeleteModel(
            name='StandardDeductionsInputs',
        ),
        migrations.AlterField(
            model_name='outputurl',
            name='unique_inputs',
            field=models.ForeignKey(default=None, to='taxbrain.TaxSaveInputs'),
        ),
        migrations.DeleteModel(
            name='PersonalExemptionsInputs',
        ),
    ]
