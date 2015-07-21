# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0065_auto_20150314_2133'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='standard_amount_single',
            new_name='_STD_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='standard_amount_jointly',
            new_name='_STD_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='standard_amount_head',
            new_name='_STD_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='standard_amount_separately',
            new_name='_STD_3',
        ),
    ]
