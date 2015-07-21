# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0017_auto_20141021_1953'),
    ]

    operations = [
        migrations.AddField(
            model_name='incomeratesinputs',
            name='dividends',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='incomeratesinputs',
            name='income_tax_rate',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='incomeratesinputs',
            name='long_term_cap',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='incomeratesinputs',
            name='medicare_unearned_inc_rate',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='incomeratesinputs',
            name='medicare_unearned_inc_threshold',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
    ]
