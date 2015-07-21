# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0008_auto_20141015_1928'),
    ]

    operations = [
        migrations.RenameField(
            model_name='outputurl',
            old_name='unique_url',
            new_name='slug',
        ),
    ]
