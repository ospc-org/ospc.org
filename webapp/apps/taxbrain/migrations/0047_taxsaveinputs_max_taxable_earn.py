# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0046_auto_20150226_1355'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='max_taxable_earn',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
