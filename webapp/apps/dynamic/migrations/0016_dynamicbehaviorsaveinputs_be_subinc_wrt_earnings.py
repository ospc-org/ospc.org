# -*- coding: utf-8 -*-


from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic', '0015_auto_20170918_1255'),
    ]

    operations = [
        migrations.AddField(
            model_name='dynamicbehaviorsaveinputs',
            name='BE_subinc_wrt_earnings',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
    ]
