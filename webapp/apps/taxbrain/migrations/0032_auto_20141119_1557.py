# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0031_auto_20141027_1516'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='taxsaveinputs',
            options={'permissions': (('view_inputs', 'Allowed to view input page.'),)},
        ),
    ]
