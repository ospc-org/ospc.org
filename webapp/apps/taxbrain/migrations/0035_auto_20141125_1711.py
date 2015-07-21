# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0034_auto_20141125_1535'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='tax_result',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
