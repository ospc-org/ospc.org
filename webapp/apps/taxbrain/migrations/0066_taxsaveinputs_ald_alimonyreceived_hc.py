# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0065_auto_20180118_2137'),
    ]

    operations = [
        # migrations.AddField(
        #     model_name='taxsaveinputs',
        #     name='ALD_AlimonyReceived_hc',
        #     field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        # ),
    ]
