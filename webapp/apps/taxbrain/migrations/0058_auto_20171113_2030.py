# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0057_auto_20171108_2245'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='tax_result',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='_tax_result',
            field=jsonfield.fields.JSONField(default=None, null=True, db_column=b'tax_result', blank=True),
        ),
    ]
