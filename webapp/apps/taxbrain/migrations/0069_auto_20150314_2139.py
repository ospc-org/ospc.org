# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0068_auto_20150314_2137'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='long_rate_one',
            new_name='_CG_rt1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='long_threshold_one_single',
            new_name='_CG_thd1_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='long_threshold_one_jointly',
            new_name='_CG_thd1_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='long_threshold_one_head',
            new_name='_CG_thd1_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='long_threshold_one_separately',
            new_name='_CG_thd1_3',
        ),
    ]
