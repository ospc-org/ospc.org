# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0066_auto_20150314_2135'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='casualty_floor',
            new_name='_ID_Casualty_frt',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='charity_ceiling_assets',
            new_name='_ID_Charity_crt_Asset',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='charity_ceiling_cash',
            new_name='_ID_Charity_crt_Cash',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='misc_floor',
            new_name='_ID_Miscellaneous_frt',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='medical_floor',
            new_name='_ID_medical_frt',
        ),
    ]
