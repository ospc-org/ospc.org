# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0018_auto_20141021_1953'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemizeddeductionsinputs',
            name='casualty_floor',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='itemizeddeductionsinputs',
            name='charity_ceiling_assets',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='itemizeddeductionsinputs',
            name='charity_ceiling_cash',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='itemizeddeductionsinputs',
            name='item_phase_out_rate',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='itemizeddeductionsinputs',
            name='item_phase_out_threshold',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='itemizeddeductionsinputs',
            name='max_perc_forfeited',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='itemizeddeductionsinputs',
            name='medical_floor',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='itemizeddeductionsinputs',
            name='misc_floor',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='itemizeddeductionsinputs',
            name='state_haircut',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='itemizeddeductionsinputs',
            name='state_limit',
            field=models.FloatField(default=None, blank=True),
            preserve_default=True,
        ),
    ]
