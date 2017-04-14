# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic', '0013_auto_20170331_2032'),
    ]

    operations = [
        migrations.AddField(
            model_name='dynamicbehaviorsaveinputs',
            name='BE_charity_0',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='dynamicbehaviorsaveinputs',
            name='BE_charity_1',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='dynamicbehaviorsaveinputs',
            name='BE_charity_2',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
    ]
