# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0033_auto_20161004_1548'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='error_text',
            field=models.ForeignKey(default=None, blank=True, to='taxbrain.ErrorMessageTaxCalculator', null=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='json_text',
            field=models.ForeignKey(default=None, blank=True, to='taxbrain.JSONReformTaxCalculator', null=True),
        ),
    ]
