# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0026_auto_20141022_1556'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='additional_child_amount',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='additional_qualify_no_child',
            field=models.FloatField(default=3, null=True, blank=True),
            preserve_default=True,
        ),
    ]
