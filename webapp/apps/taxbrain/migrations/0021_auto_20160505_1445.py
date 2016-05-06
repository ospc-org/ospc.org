# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0020_workernodescounter'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='EITC_MaxEligAge',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='EITC_MaxEligAge_cpi',
            field=models.NullBooleanField(default=None),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='EITC_MinEligAge',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='EITC_MinEligAge_cpi',
            field=models.NullBooleanField(default=None),
        ),
    ]
