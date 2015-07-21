# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0085_auto_20150314_2208'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='eitc_phase_out_threshold_0',
            new_name='_EITC_ps_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='eitc_phase_out_threshold_1',
            new_name='_EITC_ps_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='eitc_phase_out_threshold_2',
            new_name='_EITC_ps_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='eitc_phase_out_threshold_3',
            new_name='_EITC_ps_3',
        ),
    ]
