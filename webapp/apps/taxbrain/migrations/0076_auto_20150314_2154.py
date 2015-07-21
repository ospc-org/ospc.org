# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0075_auto_20150314_2149'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_2_single',
            new_name='_II_brk2_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_2_jointly',
            new_name='_II_brk2_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_2_head',
            new_name='_II_brk2_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_2_separately',
            new_name='_II_brk2_3',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_rate_2',
            new_name='_II_rt2',
        ),
    ]
