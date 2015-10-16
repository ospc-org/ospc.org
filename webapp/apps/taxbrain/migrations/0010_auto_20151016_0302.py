# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0009_auto_20151015_0340'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_0',
            field=models.CharField(default=b'True', max_length=50, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_1',
            field=models.CharField(default=b'True', max_length=50, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_2',
            field=models.CharField(default=b'True', max_length=50, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_3',
            field=models.CharField(default=b'True', max_length=50, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_4',
            field=models.CharField(default=b'True', max_length=50, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_5',
            field=models.CharField(default=b'True', max_length=50, null=True, blank=True),
        ),
    ]
