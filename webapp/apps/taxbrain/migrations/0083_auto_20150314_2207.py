# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0082_auto_20150314_2206'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='eitc_credit_rate_0',
            new_name='_EITC_rt_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='eitc_credit_rate_1',
            new_name='_EITC_rt_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='eitc_credit_rate_2',
            new_name='_EITC_rt_2',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='eitc_credit_rate_3',
        ),
    ]
