# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic', '0006_dynamicsaveinputs_micro_sim'),
    ]

    operations = [
        migrations.AddField(
            model_name='dynamicsaveinputs',
            name='guids',
            field=webapp.apps.taxbrain.models.SeparatedValuesField(default=None, null=True, blank=True),
        ),
    ]
