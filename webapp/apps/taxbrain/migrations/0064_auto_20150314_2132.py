# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0063_auto_20150314_2129'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='alimony_paid',
            new_name='_ALD_Alimony_HC',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='forfeit_int_penalty',
            new_name='_ALD_EarlyWithdraw_HC',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='keogh_sep_deduc',
            new_name='_ALD_KEOGH_SEP_HC',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='self_employ_health_deduc',
            new_name='_ALD_SelfEmp_HealthIns_HC',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='deduc_self_employ',
            new_name='_ALD_SelfEmploymentTax_HC',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='student_loan_deduc',
            new_name='_ALD_StudentLoan_HC',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='foreign_earned_inc_exemp',
            new_name='_FEI_ec_c',
        ),
    ]
