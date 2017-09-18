# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0053_auto_20170725_2141'),
    ]

    operations = [
        migrations.AddField(
            model_name='outputurl',
            name='webapp_vers',
            field=models.CharField(default=None, max_length=50, null=True, blank=True),
        ),
    ]
