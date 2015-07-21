# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0004_outputurl'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='parameters',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='exemp_start',
            field=models.FloatField(default=None),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='personal_exemp',
            field=models.FloatField(default=None),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='phase_out',
            field=models.FloatField(default=None),
            preserve_default=True,
        ),
    ]
