# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0023_taxsaveinputs_id_medical_frt_add4aged'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='quick_calc',
            field=models.BooleanField(default=False),
        ),
    ]
