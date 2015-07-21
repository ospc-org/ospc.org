# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0012_auto_20141020_1540'),
    ]

    operations = [
        migrations.AlterField(
            model_name='outputurl',
            name='slug',
            field=models.SlugField(max_length=100),
        ),
    ]
