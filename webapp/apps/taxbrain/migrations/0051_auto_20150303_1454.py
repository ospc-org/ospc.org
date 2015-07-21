# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0050_auto_20150303_1452'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='additional_aged',
            new_name='additional_aged_single',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='standard_amount',
            new_name='standard_amount_single',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='additional_aged_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='additional_aged_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='additional_aged_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='standard_amount_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='standard_amount_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='standard_amount_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
