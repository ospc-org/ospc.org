# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0064_auto_20150314_2132'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='personal_exemp_amount',
            new_name='_II_em',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='phase_out_threshold_single',
            new_name='_II_em_ps_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='phase_out_threshold_jointly',
            new_name='_II_em_ps_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='phase_out_threshold_head',
            new_name='_II_em_ps_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='phase_out_threshold_separately',
            new_name='_II_em_ps_3',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='phase_out',
            new_name='_II_prt',
        ),
    ]
