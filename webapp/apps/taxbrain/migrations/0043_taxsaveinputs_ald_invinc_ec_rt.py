# -*- coding: utf-8 -*-


from django.db import migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0042_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ALD_InvInc_ec_rt',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
    ]
