# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0029_auto_20141022_2208'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='rate_one',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='rate_two',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='threshold_one',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='threshold_two',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='gross_income',
            field=models.FloatField(default=None, null=True, blank=True, choices=[(0.5, b'Threshold 1'), (0.85, b'Threshold 2')]),
            preserve_default=True,
        ),
    ]
