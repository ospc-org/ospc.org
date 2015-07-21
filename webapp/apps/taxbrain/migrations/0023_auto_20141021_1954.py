# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0022_auto_20141021_1954'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialsecurityinputs',
            name='fica',
            field=models.FloatField(default=None),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='socialsecurityinputs',
            name='soc_max',
            field=models.FloatField(default=None),
            preserve_default=True,
        ),
    ]
