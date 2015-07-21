# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0011_remove_outputurl_unique_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxoutput',
            name='tax_result',
            field=models.FloatField(default=None, null=True),
        ),
    ]
