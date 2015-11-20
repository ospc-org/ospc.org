# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0011_taxsaveinputs_job_ids'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='first_year',
            field=models.IntegerField(default=None, null=True),
        ),
    ]
