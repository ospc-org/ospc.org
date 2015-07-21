# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0001_squashed_0093_auto_20150326_1647'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='creation_date',
            field=models.DateTimeField(default=datetime.datetime(2015, 1, 1, 0, 0)),
        ),
    ]
