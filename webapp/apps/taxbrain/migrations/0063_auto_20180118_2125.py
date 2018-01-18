# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0062_auto_20180118_2120'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='PT_exclusion_wage_limit',
            new_name='PT_excl_wagelim_rt',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='PT_exclusion_wage_limit_cpi',
            new_name='PT_excl_wagelim_rt_cpi',
        ),
    ]
