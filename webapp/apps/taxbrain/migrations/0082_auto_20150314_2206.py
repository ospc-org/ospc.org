# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0081_auto_20150314_2204'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='amt_phase_out_start_single',
            new_name='_AMT_em_ps_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='amt_phase_out_start_jointly',
            new_name='_AMT_em_ps_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='amt_phase_out_start_head',
            new_name='_AMT_em_ps_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='amt_phase_out_start_separately',
            new_name='_AMT_em_ps_3',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='amt_rate',
            new_name='_AMT_trt1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='individual_surtax',
            new_name='_AMT_trt2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='individual_threshold',
            new_name='_AMT_tthd',
        ),
    ]
