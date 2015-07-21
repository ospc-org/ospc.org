# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0048_auto_20150303_1450'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='medicare_additional_threshold',
            new_name='medicare_additional_threshold_single',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='medicare_additional_threshold_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='medicare_additional_threshold_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='medicare_additional_threshold_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
