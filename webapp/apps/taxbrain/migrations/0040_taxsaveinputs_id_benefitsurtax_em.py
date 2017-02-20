# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0039_auto_20170111_2216'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_em',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
    ]
