# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0025_auto_20141021_2124'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='amt_phase_out',
            field=models.FloatField(default=0.025, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='amt_rate',
            field=models.FloatField(default=0.26, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='casualty_floor',
            field=models.FloatField(default=0.1, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='charity_ceiling_assets',
            field=models.FloatField(default=0.3, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='charity_ceiling_cash',
            field=models.FloatField(default=0.5, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='child_phase_out_rate',
            field=models.FloatField(default=0.05, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='fica',
            field=models.FloatField(default=0.153),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='individual_surtax',
            field=models.FloatField(default=0.02, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='item_phase_out_rate',
            field=models.FloatField(default=0.03, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='max_perc_forfeited',
            field=models.FloatField(default=0.08, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='medical_floor',
            field=models.FloatField(default=0.075, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='misc_floor',
            field=models.FloatField(default=0.02, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='phase_out',
            field=models.FloatField(default=0.02, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='rate_one',
            field=models.FloatField(default=0.5, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='rate_two',
            field=models.FloatField(default=0.85, blank=True),
        ),
    ]
