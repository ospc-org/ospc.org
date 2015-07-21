# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0091_auto_20150317_1820'),
    ]

    operations = [
        migrations.AddField(
            model_name='outputurl',
            name='taxcalc_vers',
            field=models.CharField(default=None, max_length=50, null=True, blank=True),
            preserve_default=True,
        ),
    ]
