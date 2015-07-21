# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0076_auto_20150314_2154'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_3_single',
            new_name='_II_brk3_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_3_jointly',
            new_name='_II_brk3_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_3_head',
            new_name='_II_brk3_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_3_separately',
            new_name='_II_brk3_3',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_rate_3',
            new_name='_II_rt3',
        ),
    ]
