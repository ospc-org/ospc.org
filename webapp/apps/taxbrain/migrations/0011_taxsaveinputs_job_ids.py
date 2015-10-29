# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0010_auto_20151016_0302'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='job_ids',
            field=webapp.apps.taxbrain.models.SeparatedValuesField(default=None, null=True, blank=True),
        ),
    ]
