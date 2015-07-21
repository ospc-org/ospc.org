# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0078_auto_20150314_2158'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_5_single',
            new_name='_II_brk5_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_5_jointly',
            new_name='_II_brk5_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_5_head',
            new_name='_II_brk5_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_5_separately',
            new_name='_II_brk5_3',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='income_tax_rate_5',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='_II_rt5',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
    ]
