# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0080_auto_20150314_2201'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='amt_amount_single',
            new_name='_AMT_em_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='amt_amount_jointly',
            new_name='_AMT_em_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='amt_amount_head',
            new_name='_AMT_em_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='amt_amount_separately',
            new_name='_AMT_em_3',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='amt_phase_out_rate',
            new_name='_AMT_prt',
        ),
    ]
