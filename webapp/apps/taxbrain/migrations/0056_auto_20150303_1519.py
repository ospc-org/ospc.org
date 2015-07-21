# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0055_auto_20150303_1511'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='amt_amount',
            new_name='amt_amount_single',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='amt_phase_out',
            new_name='amt_phase_out_rate',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='amt_phase_out_start',
            new_name='amt_phase_out_start_single',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='amt_amount_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='amt_amount_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='amt_amount_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='amt_phase_out_start_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='amt_phase_out_start_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='amt_phase_out_start_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
