# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0045_remove_taxsaveinputs_gross_income'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='archer_msa_deduc',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='foreign_housing_adjust',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='moving_exp_deduc',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='other_adjust',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='reservist_performing_artist',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='state_haircut',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='state_limit',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='total_ira_deduc',
        ),
    ]
