# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0004_outputurl_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='outputurl',
            name='model_pk',
            field=models.IntegerField(default=None, null=True),
        ),
    ]
