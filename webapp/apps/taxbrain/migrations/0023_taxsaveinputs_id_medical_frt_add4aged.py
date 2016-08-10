# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0022_auto_20160708_2229'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_Medical_frt_add4aged',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
    ]
