# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic', '0014_auto_20170413_2300'),
    ]

    operations = [
        migrations.AddField(
            model_name='dynamicbehavioroutputurl',
            name='webapp_vers',
            field=models.CharField(default=None, max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='dynamicelasticityoutputurl',
            name='webapp_vers',
            field=models.CharField(default=None, max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='dynamicoutputurl',
            name='webapp_vers',
            field=models.CharField(default=None, max_length=50, null=True, blank=True),
        ),
    ]
