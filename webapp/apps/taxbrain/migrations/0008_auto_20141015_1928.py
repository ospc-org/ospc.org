# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0007_auto_20141015_1917'),
    ]

    operations = [
        migrations.AlterField(
            model_name='outputurl',
            name='unique_url',
            field=models.SlugField(unique=True, max_length=100),
        ),
    ]
