# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0014_auto_20151124_2029'),
        ('dynamic', '0003_dynamicsaveinputs_frisch'),
    ]

    operations = [
        migrations.AddField(
            model_name='dynamicsaveinputs',
            name='micro_sim',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='taxbrain.TaxSaveInputs', null=True),
        ),
    ]
