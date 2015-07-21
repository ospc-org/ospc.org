# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0005_auto_20141015_1455'),
    ]

    operations = [
        migrations.AddField(
            model_name='outputurl',
            name='unique_inputs',
            field=models.ForeignKey(default=None, to='taxbrain.TaxSaveInputs'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='outputurl',
            name='unique_output',
            field=models.ForeignKey(default=None, to='taxbrain.TaxOutput'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='outputurl',
            name='unique_url',
            field=models.SlugField(default=None),
            preserve_default=True,
        ),
    ]
