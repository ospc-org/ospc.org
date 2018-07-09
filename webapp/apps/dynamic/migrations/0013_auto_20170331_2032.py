# -*- coding: utf-8 -*-


from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic', '0012_auto_20160616_1908'),
    ]

    operations = [
        migrations.AddField(
            model_name='dynamicbehaviorsaveinputs',
            name='BE_charity_itemizers',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='dynamicbehaviorsaveinputs',
            name='BE_charity_non_itemizers',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
    ]
