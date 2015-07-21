# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0052_auto_20150303_1456'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='long_threshold_one',
            new_name='long_threshold_one_single',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='long_threshold_three',
            new_name='long_threshold_three_single',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='long_threshold_two',
            new_name='long_threshold_two_single',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='long_threshold_one_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='long_threshold_one_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='long_threshold_one_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='long_threshold_three_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='long_threshold_three_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='long_threshold_three_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='long_threshold_two_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='long_threshold_two_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='long_threshold_two_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
