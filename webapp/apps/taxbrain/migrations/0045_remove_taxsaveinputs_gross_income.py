# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0044_auto_20150226_1353'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='gross_income',
        ),
    ]
