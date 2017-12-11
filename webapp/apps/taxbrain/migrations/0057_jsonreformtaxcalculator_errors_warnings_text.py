# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0056_auto_20171120_2123'),
    ]

    operations = [
        migrations.AddField(
            model_name='jsonreformtaxcalculator',
            name='errors_warnings_text',
            field=models.TextField(blank=True),
        ),
    ]
