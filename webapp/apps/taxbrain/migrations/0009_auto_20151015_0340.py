# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0008_auto_20151014_2303'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_0',
            field=models.CharField(default=None, max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_1',
            field=models.CharField(default=None, max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_2',
            field=models.CharField(default=None, max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_3',
            field=models.CharField(default=None, max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_4',
            field=models.CharField(default=None, max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_5',
            field=models.CharField(default=None, max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_crt',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_trt',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='growth_choice',
            field=models.CharField(default=None, max_length=50, null=True, blank=True),
        ),
    ]
