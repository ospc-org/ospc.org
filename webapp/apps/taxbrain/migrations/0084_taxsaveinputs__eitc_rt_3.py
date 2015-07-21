# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0083_auto_20150314_2207'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='_EITC_rt_3',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
    ]
