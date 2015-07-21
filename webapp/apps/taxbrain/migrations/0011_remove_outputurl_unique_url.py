# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0010_outputurl_unique_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='outputurl',
            name='unique_url',
        ),
    ]
