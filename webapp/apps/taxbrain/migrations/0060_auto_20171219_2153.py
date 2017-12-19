# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0059_auto_20171216_2123'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='DependentCredit_before_CTC',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
    ]
