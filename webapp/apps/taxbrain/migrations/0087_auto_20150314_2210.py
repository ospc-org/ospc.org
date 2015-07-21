# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0086_auto_20150314_2208'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='qualify_number_child',
            new_name='_ACTC_ChildNum',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='additional_child_rate',
            new_name='_ACTC_rt',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='child_max_credit',
            new_name='_CTC_c',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='child_phase_out_rate',
            new_name='_CTC_prt',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='child_phase_out_threshold_single',
            new_name='_CTC_ps_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='child_phase_out_threshold_jointly',
            new_name='_CTC_ps_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='child_phase_out_threshold_head',
            new_name='_CTC_ps_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='child_phase_out_threshold_separately',
            new_name='_CTC_ps_3',
        ),
    ]
