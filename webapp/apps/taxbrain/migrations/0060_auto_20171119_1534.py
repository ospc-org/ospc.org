# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0059_taxsaveinputs_cpi_offset'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='DependentCredit_before_CTC',
            field=models.CharField(default=b'False', max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_exclusion_rt',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_exclusion_wage_limit',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
    ]
