# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0006_auto_20141015_1855'),
    ]

    operations = [
        migrations.AlterField(
            model_name='outputurl',
            name='unique_url',
            field=models.SlugField(default=None, max_length=100),
        ),
    ]
