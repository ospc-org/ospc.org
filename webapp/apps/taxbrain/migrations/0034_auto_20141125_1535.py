# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0033_auto_20141119_1601'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='outputurl',
            name='unique_output',
        ),
        migrations.DeleteModel(
            name='TaxOutput',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='tax_result',
            field=models.FloatField(default=None, null=True),
            preserve_default=True,
        ),
    ]
