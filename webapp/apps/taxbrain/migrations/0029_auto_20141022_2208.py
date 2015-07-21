# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0028_auto_20141022_1603'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='dividends',
            field=models.FloatField(default=None, null=True, blank=True, choices=[(0.0, b'Threshold 1'), (0.15, b'Threshold 2'), (0.2, b'Threshold 3')]),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='income_tax_rate',
            field=models.FloatField(default=None, null=True, blank=True, choices=[(0.0, b'Threshold 1'), (0.0, b'Threshold 2'), (0.0, b'Threshold 3'), (0.0, b'Threshold 4'), (0.0, b'Threshold 5'), (0.0, b'Threshold 6')]),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='long_term_cap',
            field=models.FloatField(default=None, null=True, blank=True, choices=[(0.15, b'Threshold 1'), (0.25, b'Threshold 2'), (0.28, b'Threshold 3')]),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='medicare_unearned_inc_rate',
            field=models.FloatField(default=0.038, null=True, blank=True),
        ),
    ]
