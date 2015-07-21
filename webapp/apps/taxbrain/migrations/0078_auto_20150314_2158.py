# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0077_auto_20150314_2156'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_4_single',
            new_name='_II_brk4_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_4_jointly',
            new_name='_II_brk4_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_4_head',
            new_name='_II_brk4_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_4_separately',
            new_name='_II_brk4_3',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_rate_4',
            new_name='_II_rt4',
        ),
    ]
