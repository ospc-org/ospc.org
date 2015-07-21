# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0067_auto_20150314_2136'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='max_perc_forfeited',
            new_name='_ID_crt',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='item_phase_out_threshold_single',
            new_name='_ID_pe_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='item_phase_out_threshold_jointly',
            new_name='_ID_pe_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='item_phase_out_threshold_head',
            new_name='_ID_pe_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='item_phase_out_threshold_separately',
            new_name='_ID_pe_3',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='item_phase_out_rate',
            new_name='_ID_prt',
        ),
    ]
