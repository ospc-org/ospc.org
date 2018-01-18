# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0057_jsonreformtaxcalculator_errors_warnings_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='CTC_new_refund_limited_all_payroll',
            field=models.CharField(default=b'False', max_length=50, null=True, blank=True),
        ),
    ]
