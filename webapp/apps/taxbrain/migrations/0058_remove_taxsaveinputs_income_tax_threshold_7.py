# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0057_auto_20150303_1525'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_7',
        ),
    ]
