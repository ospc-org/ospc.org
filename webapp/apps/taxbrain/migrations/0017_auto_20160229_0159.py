# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0016_taxsaveinputs_job_not_ready'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='job_not_ready',
            new_name='jobs_not_ready',
        ),
    ]
