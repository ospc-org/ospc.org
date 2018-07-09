# -*- coding: utf-8 -*-


from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0044_auto_20170207_1927'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ALD_InvInc_ec_base_RyanBrady',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
    ]
