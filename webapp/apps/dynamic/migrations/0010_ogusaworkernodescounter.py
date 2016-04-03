# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic', '0009_auto_20160224_0420'),
    ]

    operations = [
        migrations.CreateModel(
            name='OGUSAWorkerNodesCounter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('singleton_enforce', models.IntegerField(default=1, unique=True)),
                ('current_idx', models.IntegerField(default=0)),
            ],
        ),
    ]
