# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0084_taxsaveinputs__eitc_rt_3'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='eitc_phase_out_rate_0',
            new_name='_EITC_prt_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='eitc_phase_out_rate_1',
            new_name='_EITC_prt_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='eitc_phase_out_rate_2',
            new_name='_EITC_prt_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='eitc_phase_out_rate_3',
            new_name='_EITC_prt_3',
        ),
    ]
