# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0040_auto_20150204_1504'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='tax_result',
            field=jsonfield.fields.JSONField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
