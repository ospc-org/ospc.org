# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0051_auto_20150303_1454'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='item_phase_out_threshold',
            new_name='item_phase_out_threshold_single',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='item_phase_out_threshold_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='item_phase_out_threshold_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='item_phase_out_threshold_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
