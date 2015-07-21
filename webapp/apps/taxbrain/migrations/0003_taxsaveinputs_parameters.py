# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0002_taxoutput_tax_result'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='parameters',
            field=models.TextField(default=None),
            preserve_default=True,
        ),
    ]
