# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0007_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_0',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_1',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_2',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_3',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_4',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_5',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_crt',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_trt',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='growth_choice',
            field=models.IntegerField(default=None, null=True),
        ),
    ]
