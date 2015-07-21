# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0079_auto_20150314_2200'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_6_single',
            new_name='_II_brk6_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_6_jointly',
            new_name='_II_brk6_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_6_head',
            new_name='_II_brk6_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_6_separately',
            new_name='_II_brk6_3',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_rate_6',
            new_name='_II_rt6',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_rate_7',
            new_name='_II_rt7',
        ),
    ]
