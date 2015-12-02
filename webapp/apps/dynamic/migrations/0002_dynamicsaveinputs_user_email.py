# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dynamicsaveinputs',
            name='user_email',
            field=models.CharField(default=None, max_length=50, null=True, blank=True),
        ),
    ]
