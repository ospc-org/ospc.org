# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0067_auto_20180119_1513'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='UBI2',
            new_name='UBI_1820',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='UBI3',
            new_name='UBI_21',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='UBI1',
            new_name='UBI_u18',
        ),
    ]
