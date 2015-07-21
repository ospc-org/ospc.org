# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0074_auto_20150314_2147'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_1_single',
            new_name='_II_brk1_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_1_jointly',
            new_name='_II_brk1_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_1_head',
            new_name='_II_brk1_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_1_separately',
            new_name='_II_brk1_3',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_rate_1',
            new_name='_II_rt1',
        ),
    ]
