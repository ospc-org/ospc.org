# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0009_auto_20141020_1327'),
    ]

    operations = [
        migrations.AddField(
            model_name='outputurl',
            name='unique_url',
            field=models.CharField(default=None, unique=True, max_length=100),
            preserve_default=True,
        ),
    ]
