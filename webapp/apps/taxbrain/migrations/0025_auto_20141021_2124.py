# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0024_auto_20141021_2116'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='amount',
            new_name='personal_exemp_amount',
        ),
    ]
