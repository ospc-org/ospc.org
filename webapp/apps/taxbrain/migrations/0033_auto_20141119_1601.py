# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0032_auto_20141119_1557'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='taxsaveinputs',
            options={'permissions': (('view_inputs', 'Allowed to view Taxbrain.'),)},
        ),
    ]
