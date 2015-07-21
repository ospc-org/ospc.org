# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0043_auto_20150226_1349'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='additional_child_amount',
            new_name='additional_child_rate',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='additional_qualify_no_child',
            new_name='qualify_number_child',
        ),
    ]
