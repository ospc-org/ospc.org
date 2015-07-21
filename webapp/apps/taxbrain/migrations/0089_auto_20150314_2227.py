# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0088_auto_20150314_2216'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='long_threshold_three_head',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='long_threshold_three_jointly',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='long_threshold_three_separately',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='long_threshold_three_single',
        ),
    ]
