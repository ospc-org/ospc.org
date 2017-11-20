# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0060_auto_20171119_1534'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_exclusion_wage_limit_cpi',
            field=models.NullBooleanField(default=None),
        ),
    ]
