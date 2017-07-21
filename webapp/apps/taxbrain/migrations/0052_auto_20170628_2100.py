# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0051_auto_20170616_1424'),
    ]

    operations = [
        migrations.AddField(
            model_name='jsonreformtaxcalculator',
            name='raw_assumption_text',
            field=models.CharField(max_length=4000, blank=True),
        ),
        migrations.AddField(
            model_name='jsonreformtaxcalculator',
            name='raw_reform_text',
            field=models.CharField(max_length=4000, blank=True),
        ),
    ]
