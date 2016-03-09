# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0018_auto_20160308_1547'),
    ]

    operations = [
        migrations.AddField(
            model_name='outputurl',
            name='exp_comp_datetime',
            field=models.DateTimeField(default=datetime.datetime(2015, 1, 1, 0, 0)),
        ),
    ]
